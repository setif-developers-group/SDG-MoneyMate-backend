"""
Chatbot Agent Tools

These are the function tools available to the Chatbot Agent.
"""

from typing import Optional
from django.contrib.auth.models import User


# ============================================================================
# USER PROFILE EDITING TOOL
# ============================================================================

def edit_user_profile(
    user: User,
    monthly_income: Optional[float] = None,
    savings: Optional[float] = None,
    investments: Optional[float] = None,
    debts: Optional[float] = None,
    personal_info: Optional[dict] = None,
    user_ai_preferences: Optional[dict] = None,
    extra_info: Optional[dict] = None
) -> dict:
    """
    Edit the user's profile information.
    
    Args:
        user: The Django User object
        monthly_income: Updated monthly income
        savings: Updated savings amount
        investments: Updated investments amount
        debts: Updated debts amount
        personal_info: Updated personal information (JSON)
        user_ai_preferences: Updated AI preferences (JSON)
        extra_info: Updated extra information (JSON)
        
    Returns:
        Dictionary with success status and updated profile data
    """
    try:
        profile = user.user_profile
        
        # Update fields if provided
        if monthly_income is not None:
            profile.monthly_income = monthly_income
        if savings is not None:
            profile.savings = savings
        if investments is not None:
            profile.investments = investments
        if debts is not None:
            profile.debts = debts
        if personal_info is not None:
            profile.personal_info = personal_info
        if user_ai_preferences is not None:
            profile.user_ai_preferences = user_ai_preferences
        if extra_info is not None:
            profile.extra_info = extra_info
            
        profile.save()
        
        return {
            "type": "success",
            "data": {
                "message": "Profile updated successfully",
                "profile": {
                    "monthly_income": float(profile.monthly_income) if profile.monthly_income else None,
                    "savings": float(profile.savings) if profile.savings else None,
                    "investments": float(profile.investments) if profile.investments else None,
                    "debts": float(profile.debts) if profile.debts else None,
                    "personal_info": profile.personal_info,
                    "user_ai_preferences": profile.user_ai_preferences,
                    "extra_info": profile.extra_info
                }
            }
        }
    except Exception as e:
        return {
            "type": "error",
            "data": {"error": f"Failed to update profile: {str(e)}"}
        }


# ============================================================================
# MAIN AI COORDINATOR CALL TOOL
# ============================================================================

def call_main_coordinator(user: User, message: str) -> dict:
    """
    Call the Main AI Coordinator to handle complex tasks.
    
    This function allows the chatbot to delegate complex tasks to the Main AI
    Coordinator, which will orchestrate the appropriate specialized agents.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Main AI Coordinator
        
    Returns:
        Dictionary with the coordinator's response
    """
    from ai_core.services import process_coordinator_message
    
    result = process_coordinator_message(user, message)
    return result


def call_expense_manager(user: User, message: str) -> dict:
    """
    Call the Expense Manager Agent to track and manage expenses.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Expense Manager
        
    Returns:
        Dictionary with the Expense Manager's response
    """
    from expense.services import process_expense_management
    return process_expense_management(user, message)


def call_report_agent(user: User, message: str) -> dict:
    """
    Call the Report Agent to generate financial reports.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Report Agent
        
    Returns:
        Dictionary with the Report Agent's response
    """
    from expense.services import process_report_generation
    return process_report_generation(user, message)


# ============================================================================
# FUNCTION DECLARATIONS FOR GEMINI API
# ============================================================================

edit_user_profile_declaration = {
    "name": "edit_user_profile",
    "description": "Edits the user's profile information including financial data and preferences. Use this when the user wants to update their income, savings, investments, debts, or personal preferences.",
    "parameters": {
        "type": "object",
        "properties": {
            "monthly_income": {
                "type": "number",
                "description": "The user's monthly income amount."
            },
            "savings": {
                "type": "number",
                "description": "The user's current savings amount."
            },
            "investments": {
                "type": "number",
                "description": "The user's current investments amount."
            },
            "debts": {
                "type": "number",
                "description": "The user's current debts amount."
            },
            "personal_info": {
                "type": "object",
                "description": "Personal information as a JSON object (e.g., preferred_currency, location_context)."
            },
            "user_ai_preferences": {
                "type": "object",
                "description": "AI preferences as a JSON object (e.g., tone, style, communication preferences)."
            },
            "extra_info": {
                "type": "object",
                "description": "Additional information as a JSON object."
            }
        },
        "required": []  # All fields are optional
    }
}

call_main_coordinator_declaration = {
    "name": "call_main_coordinator",
    "description": "Calls the Main AI Coordinator to handle complex tasks that require coordination between multiple agents or specialized financial operations (budgets, forecasts, etc.). Use this when the user's request involves budgets, financial planning, or tasks beyond simple conversation.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The request or task to delegate to the Main AI Coordinator."
            }
        },
        "required": ["message"]
    }
}

call_expense_manager_declaration = {
    "name": "call_expense_manager",
    "description": "Calls the Expense Manager Agent to track and record user expenses. Use this when the user mentions spending money, making a purchase, or wants to track an expense. Examples: 'I spent 500 at a coffee shop', 'Add expense of 200 for groceries', 'Track my purchase of 1000 for electronics'.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The user's expense description including amount, item/category, and any other details. Pass the user's message directly."
            }
        },
        "required": ["message"]
    }
}

call_report_agent_declaration = {
    "name": "call_report_agent",
    "description": "Calls the Report Agent to generate financial reports.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The request for the report."
            }
        },
        "required": ["message"]
    }
}
