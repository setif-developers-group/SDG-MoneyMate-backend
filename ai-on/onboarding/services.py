"""
Onboarding Agent Service

Handles the creation and management of the onboarding AI agent.
"""

from agents.models import agentModel
from agents.services import register_agent_function, build_config, execute_function, get_agent_history, add_to_history
from .tools import (
    ask_question, 
    ask_question_declaration,
    finish_onboarding_and_save_info,
    finish_onboarding_declaration
)
from django.contrib.auth.models import User
from google import genai
from google.genai import types
from decouple import config

API_KEY = config('GEMINI_API_KEY')

ONBOARDING_SYSTEM_INSTRUCTION = '''
IDENTITY
You are the **Onboarding Agent** in the AION personal finance management system. Your sole purpose is to collect required financial information from new users and hand them off to the main system.

THE AION SYSTEM CONTEXT
You are the crucial first step for AION, a multi-agent personal finance management application. After you successfully collect the initial data, the user will interact with the **Chatbot Agent**, which relies on the complete profile you create to coordinate powerful analytical agents like the **Main AI Coordinator**, **Budget Sentinel**, and **Planner & Forecaster**. The system operates with **DZD (Algerian Dinars)** as the default currency, but you must confirm and respect the user's preferred currency in the `personal_info` field.

YOUR ROLE IN THE SYSTEM
The AION system needs specific financial data before users can start tracking expenses and managing budgets. You collect this data through a friendly conversation and structure it for the backend. After you are satisfied with the collected data, you will call `finish_onboarding_and_save_info()`.

WHAT YOU DO
* Ask clear, structured questions to collect required user information.
* **Use the ask_question() function to ask only 1 question at a time (do not ask more than one question per turn).**
* Explain why you need each piece of information.
* Be encouraging and patient.
* **Build the 'Preferred budget categories' by asking questions to understand the user's spending needs and priorities (this will be part of the Extra Info or Personal Info structure).**
* Structure all collected data properly.
* **Call finish_onboarding_and_save_info() when you believe you have all necessary information and fully understand the client's financial profile and goals.**

REQUIRED DATA YOU MUST COLLECT (MINIMUM)
These are the absolute minimum required fields. You must ask additional questions to gather rich data for all fields.
1.  **Monthly Income, Savings, Investments, Debts** (4 distinct float values).
2.  **User AI Preferences** (dict: must include 'risk_preference', 'tone', 'style').
3.  **Personal Info** (dict: must include 'preferred_currency' (default DZD) and 'location_context').
4.  **Extra Info** (dict: all non-core financial details, goals, habits, and specific requirements).
5.  **AI Summary** (str: 2-4 sentence summary).

WHAT YOU DON'T DO
* Don't create budgets (the backend handles this after you finish), but you must collect specific budget minimums if the user has a requirement (e.g., 'car budget at least 10000DA') and include it in **extra_info**.
* **Don't assume any financial information or user preferences—always ask the user.**
* **Don't ask more than 1 question at once.**

PERSONALITY & TONE
Friendly and welcoming, Clear and concise, Patient and encouraging, Professional but warm. Explain the "why" behind each question.
'''


def get_or_create_onboarding_agent() -> agentModel:
    """
    Get or create the onboarding agent and register its functions.
    
    Returns:
        The onboarding agent model instance
    """
    agent, created = agentModel.objects.get_or_create(
        name="onboarding_agent",
        defaults={
            "description": "Collects financial information from new users during onboarding",
            "system_instruction": ONBOARDING_SYSTEM_INSTRUCTION,
            "gemini_model": "gemini-2.0-flash",
            "thinking_budget": 0
        }
    )
    
    
    # Register functions if newly created or not already registered
    register_agent_function(
        agent_id=agent.id,
        func_name="ask_question",
        function_declaration=ask_question_declaration,
        function=ask_question
    )
    
    register_agent_function(
        agent_id=agent.id,
        func_name="finish_onboarding_and_save_info",
        function_declaration=finish_onboarding_declaration,
        function=finish_onboarding_and_save_info
    )
    
    return agent


def process_onboarding_turn(user: User, user_message: str = None) -> dict:
    """
    Process one turn of the onboarding conversation.
    
    Args:
        user: The Django User object
        user_message: The user's message/answer (None for first turn)
        
    Returns:
        Dictionary with either:
        - {"type": "question", "data": {question, question_type, options}}
        - {"type": "completed", "data": {success, message}}
        - {"type": "error", "data": {error}}
    """
    print(f"DEBUG: Onboarding Agent is running now... processing message: {user_message}")
    # Get or create agent
    agent = get_or_create_onboarding_agent()
    
    # Get conversation history
    history = get_agent_history(agent, user)
    
    # Add user message to history if provided
    if user_message:
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
    
    # Ensure the last message is from the user (Gemini API requirement)
    if not history or history[-1].role == "model":
        start = "start"
        add_to_history(
            agent=agent,
            user=user,
            part={"parts": [{"text": start}]},
            role="user"
        )
        history.append(types.Content(
            role="user",
            parts=[types.Part(text=start)]
        ))
    
    # Build config
    config_obj = build_config(agent)
    
    # Create Gemini client
    client = genai.Client(api_key=API_KEY)
    
    # Generate response
    response = client.models.generate_content(
        model=agent.gemini_model,
        contents=history,
        config=config_obj
    )
    
    # Save model response to history
    add_to_history(
        agent=agent,
        user=user,
        part={"parts": [{"text": response.text if response.text else ""}]},
        role="model"
    )
    
    # Check if there are function calls
    if response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                func_call = part.function_call
                func_name = func_call.name
                func_args = dict(func_call.args)
                
                # Add user to args for finish_onboarding
                if func_name == "finish_onboarding_and_save_info":
                    func_args['user'] = user
                
                
                # Execute the function
                print(f"DEBUG: Onboarding Agent calling {func_name} with args: {func_args}...")
                result = execute_function(agent, func_name, func_args)
                
                # If it's ask_question, return the question
                if func_name == "ask_question":
                    return {
                        "type": "question",
                        "data": result
                    }
                
                # If it's finish_onboarding, return completion
                elif func_name == "finish_onboarding_and_save_info":
                    return {
                        "type": "finsh",
                        "data": result
                    }
    
    # If no function call, return error
    return {
        "type": "error",
        "data": {"error": "Agent did not call a function. Please try again."}
    }
