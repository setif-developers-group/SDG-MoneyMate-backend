"""
Main AI Coordinator Service

Handles the creation and management of the Main AI Coordinator agent.
This agent acts as the central orchestrator for all other agents in the AION system.
"""

from agents.models import agentModel
from agents.services import register_agent_function, build_config, execute_function, get_agent_history, add_to_history
from .tools import (
    call_budget_agent,
    call_budget_agent_declaration,
    send_message_to_agent,
    send_message_to_agent_declaration
)
from django.contrib.auth.models import User
from google import genai
from google.genai import types
from decouple import config

API_KEY = config('GEMINI_API_KEY')

COORDINATOR_SYSTEM_INSTRUCTION = '''
IDENTITY
You are the **Main AI Coordinator**, the backend orchestrator of the AION system.
**CRITICAL**: You NEVER communicate with the end-user directly. Your only interface is with other AI agents (like the Chatbot).

YOUR MISSION
Your job is to receive high-level directives from user-facing agents (like the Chatbot) and execute them by managing and commanding specialized worker agents (like the Budget Agent).

OPERATIONAL WORKFLOW
1.  **Receive Directive**: You get a task from an agent (e.g., "The user wants to lower their grocery budget").
2.  **Formulate Plan**: Decide which worker agent(s) need to be involved.
3.  **Execute Commands**: Use `send_message_to_agent` (or specific tools like `call_budget_agent`) to give specific, actionable instructions to the worker agents.
    *   *Example*: "Budget Agent, update the 'Groceries' category to 15,000 DZD."
4.  **Report Results**: Return a concise summary of the actions taken and the outcomes to the calling agent.

AVAILABLE WORKER AGENTS
*   **Budget Agent**: Handles all budget creation, updates, deletion, and rebalancing.
*   **Forecast Agent**: Future financial planning.
*   **Product Advisor**: Financial product recommendations.
*   **Notification Agent**: Sending alerts.
*   (And others as available via `send_message_to_agent`)

GUIDELINES
*   **Be Directive**: You are the manager. Tell the worker agents exactly what to do.
*   **No Small Talk**: Do not be conversational. Be functional and efficient.
*   **Delegate**: Do not try to do the math or database updates yourself. Always call the specialized agent.
*   **Output**: Your final response should be a status report to the Chatbot, enabling it to inform the user (e.g., "Budget updated successfully. New total is X.").
'''


def get_or_create_coordinator_agent() -> agentModel:
    """
    Get or create the Main AI Coordinator agent and register its functions.
    
    Returns:
        The coordinator agent model instance
    """
    agent, created = agentModel.objects.get_or_create(
        name="main_ai_coordinator",
        defaults={
            "description": "Central orchestrator that coordinates all specialized agents in the AION system",
            "system_instruction": COORDINATOR_SYSTEM_INSTRUCTION,
            "gemini_model": "gemini-2.5-flash-lite",
            "thinking_budget": 0
        }
    )
    
    # Update model if it exists but configuration is different
    if not created and (agent.gemini_model != "gemini-2.5-flash-lite" or agent.thinking_budget != 0):
        agent.gemini_model = "gemini-2.5-flash-lite"
        agent.thinking_budget = 0
        agent.save()
    
    # Register functions
    register_agent_function(
        agent_id=agent.id,
        func_name="call_budget_agent",
        function_declaration=call_budget_agent_declaration,
        function=call_budget_agent
    )
    
    register_agent_function(
        agent_id=agent.id,
        func_name="send_message_to_agent",
        function_declaration=send_message_to_agent_declaration,
        function=send_message_to_agent
    )
    
    return agent


def process_coordinator_message(user: User, user_message: str) -> dict:
    """
    Process a message sent to the Main AI Coordinator.
    
    Args:
        user: The Django User object
        user_message: The user's message/request
        
    Returns:
        Dictionary with either:
        - {"type": "response", "data": {"message": str, "agent_called": str|None}}
        - {"type": "error", "data": {"error": str}}
    """
    print(f"DEBUG: Main AI Coordinator is running now... processing message: {user_message}")
    # Get or create agent
    agent = get_or_create_coordinator_agent()
    
    # Get conversation history
    history = get_agent_history(agent, user)
    
    # Add user message to history
    add_to_history(
        agent=agent,
        user=user,
        part={"parts": [{"text": user_message}]},
        role="user"
    )
    history.append(types.Content(
        role="user",
        parts=[types.Part(text=user_message)]
    ))
    
    # Build config
    config_obj = build_config(agent)
    
    # Create Gemini client
    client = genai.Client(api_key=API_KEY)
    
    # Track which agents were called
    agents_called = []
    
    # Generate response (may involve multiple function calls)
    max_iterations = 5  # Prevent infinite loops
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        response = client.models.generate_content(
            model=agent.gemini_model,
            contents=history,
            config=config_obj
        )
        
        # Check if there are function calls
        has_function_call = False
        if response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    has_function_call = True
                    func_call = part.function_call
                    func_name = func_call.name
                    func_args = dict(func_call.args)
                    
                    # Add user to args for function execution
                    func_args['user'] = user
                    
                    # Track which agent is being called
                    if func_name == "call_budget_agent":
                        agents_called.append("budget_agent")
                    elif func_name == "send_message_to_agent":
                        agents_called.append(func_args.get('agent_name', 'unknown'))
                    
                    # Execute the function
                    print(f"DEBUG: Main AI Coordinator calling {func_name} with args: {func_args}...")
                    result = execute_function(agent, func_name, func_args)
                    
                    # Prepare args for history (without user object - not JSON serializable)
                    func_args_for_history = {k: v for k, v in func_args.items() if k != 'user'}
                    
                    # Add function call to history
                    add_to_history(
                        agent=agent,
                        user=user,
                        part={"parts": [{"function_call": {"name": func_name, "args": func_args_for_history}}]},
                        role="model"
                    )
                    
                    # Add function response to history
                    add_to_history(
                        agent=agent,
                        user=user,
                        part={"parts": [{"function_response": {"name": func_name, "response": result}}]},
                        role="user"
                    )
                    
                    # Update history for next iteration with proper types
                    history.append(types.Content(
                        role="model",
                        parts=[types.Part(function_call=types.FunctionCall(name=func_name, args=func_args_for_history))]
                    ))
                    history.append(types.Content(
                        role="user",
                        parts=[types.Part(function_response=types.FunctionResponse(name=func_name, response=result))]
                    ))
        
        # If no function call, we have the final response
        if not has_function_call:
            # Save model response to history
            add_to_history(
                agent=agent,
                user=user,
                part={"parts": [{"text": response.text if response.text else ""}]},
                role="model"
            )
            
            return {
                "type": "response",
                "data": {
                    "message": response.text if response.text else "I've processed your request.",
                    "agents_called": agents_called if agents_called else None
                }
            }
    
    # If we hit max iterations, return what we have
    return {
        "type": "error",
        "data": {
            "error": "Maximum iterations reached. Please try again with a simpler request."
        }
    }
