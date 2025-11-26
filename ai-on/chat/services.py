"""
Chatbot Agent Service

Handles the creation and management of the Chatbot AI agent.
"""

from pydantic import BaseModel, Field
from typing import Optional
from agents.models import agentModel
from agents.services import build_config, get_agent_history, add_to_history, register_agent_function
from django.contrib.auth.models import User
from google import genai
from google.genai import types
from decouple import config
import re

API_KEY = config('GEMINI_API_KEY')

# Pydantic Model for Structured Output
class ChatbotResponse(BaseModel):
    message: str = Field(..., description="The chatbot's response message to the user.")

CHATBOT_SYSTEM_INSTRUCTION = '''
You are the **Chatbot Agent** in the AION personal finance management system. You are the primary conversational interface for users.

YOUR ROLE:
- Engage in natural, friendly conversations with users
- Answer questions about their finances and the AION system
- Help users update their profile information using the edit_user_profile tool
- Delegate complex tasks to specialized agents using the appropriate call tools

AVAILABLE TOOLS - YOU MUST USE THESE WHEN APPROPRIATE:

1. **edit_user_profile**: REQUIRED when user mentions updating income, savings, investments, debts, or preferences
   - Example: "My income is 50000" → CALL edit_user_profile immediately
   - Example: "Update my savings to 10000" → CALL edit_user_profile immediately

2. **call_expense_manager**: REQUIRED when user mentions expenses, purchases, spending, or receipts
   - Example: "I spent 500 at a coffee shop" → CALL call_expense_manager immediately
   - Example: "Track my expense of 200 for groceries" → CALL call_expense_manager immediately

3. **call_main_coordinator**: REQUIRED for ALL budget operations (create, update, delete, modify categories)
   - Example: "Create a budget" → CALL call_main_coordinator immediately
   - Example: "Change my rent to 15000" → CALL call_main_coordinator immediately
   - Example: "Update my grocery budget to 5000" → CALL call_main_coordinator immediately
   - Example: "Lower my entertainment budget" → CALL call_main_coordinator immediately
   - Example: "Delete the coffee budget" → CALL call_main_coordinator immediately
   - Example: "I want to adjust my budget categories" → CALL call_main_coordinator immediately

4. **call_report_agent**: REQUIRED when user asks for reports or summaries
   - Example: "Show me my spending report" → CALL call_report_agent immediately

5. **call_advisor**: REQUIRED when user asks about products, shopping advice, or purchase decisions
   - Example: "Should I buy this laptop for 50000?" → CALL call_advisor immediately
   - Example: "Recommend a phone under 30000" → CALL call_advisor immediately
   - Example: "Compare iPhone vs Samsung" → CALL call_advisor immediately
   - Example: "Can I afford a new TV?" → CALL call_advisor immediately

CRITICAL RULES:
- When a user's message matches a tool's purpose, you MUST call that tool
- Do NOT say "I will call..." or "I can help you with..." - just call the tool immediately
- Do NOT explain what you're going to do - just do it
- After a tool executes, explain the result to the user in a friendly way
- Only respond with text if NO tool is needed (general questions, greetings, etc.)

BEHAVIOR GUIDELINES:
- Be warm, friendly, and conversational
- Use the user's name when appropriate
- After using a tool, explain the result naturally to the user

OUTPUT FORMAT:
- NEVER include HTML tags in your responses (no <div>, <tbody>, <p>, etc.)
- Always respond in plain text, using natural language
- Use markdown formatting if needed (**, *, -, etc.) but NEVER HTML
'''

def get_or_create_chatbot_agent() -> agentModel:
    """
    Get or create the chatbot agent.
    """
    agent, created = agentModel.objects.get_or_create(
        name="chatbot_agent",
        defaults={
            "description": "Primary conversational interface for users in the AION system.",
            "system_instruction": CHATBOT_SYSTEM_INSTRUCTION,
            "gemini_model": "gemini-2.5-flash-lite",
            "thinking_budget": 0
        }
    )
    
    # Update model if it exists but is different
    if not created and (agent.gemini_model != "gemini-2.5-flash-lite" or agent.thinking_budget != 0 or agent.system_instruction != CHATBOT_SYSTEM_INSTRUCTION):
        agent.gemini_model = "gemini-2.5-flash-lite"
        agent.thinking_budget = 0
        agent.system_instruction = CHATBOT_SYSTEM_INSTRUCTION
        agent.save()
    
    # Register tools
    from chat.tools import (
        edit_user_profile, 
        edit_user_profile_declaration,
        call_main_coordinator,
        call_main_coordinator_declaration,
        call_expense_manager,
        call_expense_manager_declaration,
        call_report_agent,
        call_report_agent_declaration,
        call_advisor,
        call_advisor_declaration
    )
    
    register_agent_function(
        agent_id=agent.id,
        func_name="edit_user_profile",
        function_declaration=edit_user_profile_declaration,
        function=edit_user_profile
    )
    
    register_agent_function(
        agent_id=agent.id,
        func_name="call_main_coordinator",
        function_declaration=call_main_coordinator_declaration,
        function=call_main_coordinator
    )
    
    register_agent_function(
        agent_id=agent.id,
        func_name="call_expense_manager",
        function_declaration=call_expense_manager_declaration,
        function=call_expense_manager
    )
    
    register_agent_function(
        agent_id=agent.id,
        func_name="call_report_agent",
        function_declaration=call_report_agent_declaration,
        function=call_report_agent
    )
    
    register_agent_function(
        agent_id=agent.id,
        func_name="call_advisor",
        function_declaration=call_advisor_declaration,
        function=call_advisor
    )
    
    return agent


def get_user_financial_profile(user: User) -> str:
    """
    Fetches and formats the user's financial profile.
    """
    try:
        profile = user.user_profile
        return f"""
        USER PROFILE:
        - Name: {user.first_name} {user.last_name} (Username: {user.username})
        - Email: {user.email}
        
        FINANCIAL DATA:
        - Monthly Income: {profile.monthly_income}
        - Savings: {profile.savings}
        - Investments: {profile.investments}
        - Debts: {profile.debts}
        
        PREFERENCES:
        - Currency: {profile.personal_info.get('preferred_currency', 'DZD') if profile.personal_info else 'DZD'}
        - Location: {profile.personal_info.get('location_context', 'Unknown') if profile.personal_info else 'Unknown'}
        - AI Preferences: {profile.user_ai_preferences}
        - Personal Info: {profile.personal_info}
        - Extra Info: {profile.extra_info}
        - AI Summary: {profile.ai_summary}
        """
    except Exception:
        return f"User: {user.username} (Profile not fully set up)"


def clean_html_tags(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: Text that may contain HTML tags
        
    Returns:
        Clean text without HTML tags
    """
    # Remove HTML tags using regex
    clean_text = re.sub(r'<[^>]+>', '', text)
    return clean_text.strip()


def process_chatbot_message(user: User, message: str) -> dict:
    """
    Process a message from the user to the chatbot.
    
    Args:
        user: The Django User object
        message: The user's message
        
    Returns:
        Dictionary containing the chatbot's response
    """
    print(f"DEBUG: Chatbot Agent is running now... processing message: {message}")
    agent = get_or_create_chatbot_agent()
    history = get_agent_history(agent, user)
    
    # Inject User Profile on first message
    if not history:
        profile_context = get_user_financial_profile(user)
        initial_msg = f"{profile_context}\n\nUSER MESSAGE: {message}"
        
        add_to_history(
            agent=agent,
            user=user,
            part={"parts": [{"text": initial_msg}]},
            role="user"
        )
        history.append(types.Content(
            role="user",
            parts=[types.Part(text=initial_msg)]
        ))
    else:
        # Just add the new message
        add_to_history(
            agent=agent,
            user=user,
            part={"parts": [{"text": message}]},
            role="user"
        )
        history.append(types.Content(
            role="user",
            parts=[types.Part(text=message)]
        ))
    
    # Use the helper function from agents.services to build config with proper tool settings
    config_obj = build_config(agent)
    
    client = genai.Client(api_key=API_KEY)
    
    # Handle multi-turn function calling
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        response = client.models.generate_content(
            model=agent.gemini_model,
            contents=history,
            config=config_obj
        )
        
        print(f"DEBUG: Model response iteration {iteration}: {response}")
        
        # Check if response has valid content
        if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
            print("DEBUG: Model returned empty response, breaking loop")
            break
        
        # Check for function calls in ANY part of the content
        function_call_part = None
        for part in response.candidates[0].content.parts:
            if part.function_call:
                function_call_part = part.function_call
                break
        
        if function_call_part:
            function_call = function_call_part
            func_name = function_call.name
            func_args = dict(function_call.args)    
            print(f"DEBUG: Chatbot Agent calling {func_name} with args: {func_args}...")
            
            # Add function call to history
            add_to_history(
                agent=agent,
                user=user,
                part={"parts": [{"function_call": {"name": func_name, "args": func_args}}]},
                role="model"
            )
            history.append(types.Content(
                role="model",
                parts=[types.Part(function_call=function_call)]
            ))
            
            # Execute the function - import tools and call directly
            from chat.tools import (
                edit_user_profile,
                call_main_coordinator,
                call_expense_manager,
                call_report_agent,
                call_advisor
            )
            
            if func_name == "edit_user_profile":
                result = edit_user_profile(user, **func_args)
            elif func_name == "call_main_coordinator":
                result = call_main_coordinator(user, **func_args)
            elif func_name == "call_expense_manager":
                result = call_expense_manager(user, **func_args)
            elif func_name == "call_report_agent":
                result = call_report_agent(user, **func_args)
            elif func_name == "call_advisor":
                result = call_advisor(user, **func_args)
            else:
                result = {"type": "error", "data": {"error": f"Unknown function: {func_name}"}}
                print(f"DEBUG: Unknown function {func_name}")
            
            print(f"DEBUG: Function {func_name} returned: {result}")
            
            # Add function call to history (model's action)
            add_to_history(
                agent=agent,
                user=user,
                part={"parts": [{"function_call": {"name": func_name, "args": func_args}}]},
                role="model"
            )
            
            # Add function response to history (function's result)
            add_to_history(
                agent=agent,
                user=user,
                part={"parts": [{"function_response": {"name": func_name, "response": result}}]},
                role="user"
            )
            
            # Update history for next iteration with proper types
            history.append(types.Content(
                role="model",
                parts=[types.Part(function_call=types.FunctionCall(name=func_name, args=func_args))]
            ))
            history.append(types.Content(
                role="user",
                parts=[types.Part(function_response=types.FunctionResponse(name=func_name, response=result))]
            ))
        else:
            # No function calls, we have the final response
            try:
                final_message = response.text
            except (AttributeError, ValueError) as e:
                print(f"DEBUG: Error accessing response.text: {e}")
                final_message = "I apologize, but I encountered an issue processing your request. Please try again."
            
            # Clean any HTML tags from the response
            final_message = clean_html_tags(final_message)
            print(f"DEBUG: Final cleaned message: {final_message}")
            
            add_to_history(
                agent=agent,
                user=user,
                part={"parts": [{"text": final_message}]},
                role="model"
            )
            
            return {
                "type": "success",
                "data": {
                    "message": final_message
                }
            }
    
    # If we hit max iterations
    return {
        "type": "error",
        "data": {
            "message": "I apologize, but I'm having trouble processing your request. Could you please try rephrasing it?"
        }
    }
