"""
Main AI Coordinator Tools

These are the function tools available to the Main AI Coordinator agent.
Also includes tools for OTHER agents to call the Main AI Coordinator.

All agent call functions use lazy loading to avoid circular imports.
"""

from typing import Optional, List
from django.contrib.auth.models import User


# ============================================================================
# AGENT CALL FUNCTIONS (with lazy loading to avoid circular imports)
# ============================================================================

def call_budget_agent(user: User, message: str) -> dict:
    """
    Call the Budget Agent to generate or update budgets.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Budget Agent
        
    Returns:
        Dictionary with the Budget Agent's response
    """
    # Lazy import to avoid circular dependency
    from budget.services import process_budget_generation
    
    result = process_budget_generation(user, message)
    return result


def call_chatbot_agent(user: User, message: str) -> dict:
    """
    Call the Chatbot Agent for general conversation.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Chatbot Agent
        
    Returns:
        Dictionary with the Chatbot Agent's response
    """
    # Lazy import to avoid circular dependency
    from chat.services import process_chatbot_message
    
    result = process_chatbot_message(user, message)
    return result


def call_market_watcher(user: User, message: str) -> dict:
    """
    Call the Market Watcher Agent for market analysis and trends.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Market Watcher
        
    Returns:
        Dictionary with the Market Watcher's response
    """
    # Lazy import to avoid circular dependency
    # TODO: Implement when market watcher service is created
    # from market.services import process_market_analysis
    # result = process_market_analysis(user, message)
    # return result
    
    return {
        "type": "error",
        "data": {"error": "Market Watcher agent not yet implemented"}
    }


def call_receipt_parser(user: User, message: str) -> dict:
    """
    Call the Receipt Parser Agent to parse and extract receipt data.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Receipt Parser
        
    Returns:
        Dictionary with the Receipt Parser's response
    """
    # Lazy import to avoid circular dependency
    # TODO: Implement when receipt parser service is created
    # from receipts.services import process_receipt_parsing
    # result = process_receipt_parsing(user, message)
    # return result
    
    return {
        "type": "error",
        "data": {"error": "Receipt Parser agent not yet implemented"}
    }


def call_product_advisor(user: User, message: str) -> dict:
    """
    Call the Product Advisor Agent for product recommendations.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Product Advisor
        
    Returns:
        Dictionary with the Product Advisor's response
    """
    # Lazy import to avoid circular dependency
    from advisor.services import process_advisor_request
    
    result = process_advisor_request(user, message)
    return result


def call_notification_agent(user: User, message: str) -> dict:
    """
    Call the Notification Agent to send notifications.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Notification Agent
        
    Returns:
        Dictionary with the Notification Agent's response
    """
    # Lazy import to avoid circular dependency
    from notify.services import process_notification_request
    
    result = process_notification_request(user, message)
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
    # Lazy import to avoid circular dependency
    from expense.services import process_expense_management
    
    result = process_expense_management(user, message)
    return result


def call_forecast_agent(user: User, message: str) -> dict:
    """
    Call the Forecast Agent for financial planning and forecasting.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Forecast Agent
        
    Returns:
        Dictionary with the Forecast Agent's response
    """
    # Lazy import to avoid circular dependency
    from forecast.services import process_forecast_request
    
    result = process_forecast_request(user, message)
    return result


def call_report_agent(user: User, message: str) -> dict:
    """
    Call the Report Agent to generate financial reports.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Report Agent
        
    Returns:
        Dictionary with the Report Agent's response
    """
    # Lazy import to avoid circular dependency
    from expense.services import process_report_generation
    
    result = process_report_generation(user, message)
    return result


# ============================================================================
# GENERIC AGENT MESSAGING FUNCTION
# ============================================================================

def send_message_to_agent(
    agent_name: str,
    message: str,
    user: User
) -> dict:
    """
    Send a message to any available agent in the system.
    
    This is a generic function that routes messages to specific agents.
    
    Args:
        agent_name: Name of the agent to call
        message: The message/request to send to the agent
        user: The Django User object
        
    Returns:
        Dictionary with the agent's response
        
    Raises:
        ValueError: If the agent_name is not recognized
    """
    agent_map = {
        "budget_agent": call_budget_agent,
        "chatbot_agent": call_chatbot_agent,
        "market_watcher": call_market_watcher,
        "receipt_parser": call_receipt_parser,
        "product_advisor": call_product_advisor,
        "notification_agent": call_notification_agent,
        "expense_manager": call_expense_manager,
        "forecast_agent": call_forecast_agent,
        "report_agent": call_report_agent,
    }
    
    if agent_name in agent_map:
        return agent_map[agent_name](user, message)
    else:
        raise ValueError(f"Agent '{agent_name}' is not recognized or not yet implemented.")


# ============================================================================
# TOOLS FOR OTHER AGENTS TO CALL THE MAIN AI COORDINATOR
# ============================================================================

def call_main_coordinator(user: User, message: str) -> dict:
    """
    Call the Main AI Coordinator from another agent.
    
    This function allows other agents (like the chatbot) to delegate complex
    tasks to the Main AI Coordinator, which will then orchestrate the appropriate
    specialized agents.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Main AI Coordinator
        
    Returns:
        Dictionary with the coordinator's response
    """
    from ai_core.services import process_coordinator_message
    
    result = process_coordinator_message(user, message)
    return result


# ============================================================================
# FUNCTION DECLARATIONS FOR GEMINI API
# ============================================================================

# Individual agent function declarations
call_budget_agent_declaration = {
    "name": "call_budget_agent",
    "description": "Calls the Budget Agent to generate, update, or rebalance user budgets based on financial data and goals.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The request or instruction to send to the Budget Agent."
            }
        },
        "required": ["message"]
    }
}

call_chatbot_agent_declaration = {
    "name": "call_chatbot_agent",
    "description": "Calls the Chatbot Agent for general conversation and user interaction.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The message to send to the Chatbot Agent."
            }
        },
        "required": ["message"]
    }
}

call_market_watcher_declaration = {
    "name": "call_market_watcher",
    "description": "Calls the Market Watcher Agent to analyze market trends and opportunities.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The request for market analysis."
            }
        },
        "required": ["message"]
    }
}

call_receipt_parser_declaration = {
    "name": "call_receipt_parser",
    "description": "Calls the Receipt Parser Agent to parse and extract data from receipts.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The request to parse receipt data."
            }
        },
        "required": ["message"]
    }
}

call_product_advisor_declaration = {
    "name": "call_product_advisor",
    "description": "Calls the Product Advisor Agent for product recommendations and advice.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The request for product advice."
            }
        },
        "required": ["message"]
    }
}

call_notification_agent_declaration = {
    "name": "call_notification_agent",
    "description": "Calls the Notification Agent to send notifications and alerts to the user.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The notification request."
            }
        },
        "required": ["message"]
    }
}

call_expense_manager_declaration = {
    "name": "call_expense_manager",
    "description": "Calls the Expense Manager Agent to track and manage user expenses.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The expense management request."
            }
        },
        "required": ["message"]
    }
}

call_forecast_agent_declaration = {
    "name": "call_forecast_agent",
    "description": "Calls the Forecast Agent for financial planning and forecasting.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The forecasting request."
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

# Generic send_message_to_agent declaration - can be customized per agent
def create_send_message_declaration(allowed_agents: List[str]) -> dict:
    """
    Create a send_message_to_agent declaration with specific allowed agents.
    
    Args:
        allowed_agents: List of agent names this agent can call
        
    Returns:
        Function declaration dict for Gemini API
    """
    return {
        "name": "send_message_to_agent",
        "description": "Sends a message to another specialized agent in the AION system. Use this to delegate tasks to other agents.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "enum": allowed_agents,
                    "description": f"The name of the agent to call. Available agents: {', '.join(allowed_agents)}"
                },
                "message": {
                    "type": "string",
                    "description": "The message or request to send to the specified agent."
                }
            },
            "required": ["agent_name", "message"]
        }
    }


# Default declaration for Main AI Coordinator (can call all agents except onboarding)
send_message_to_agent_declaration = create_send_message_declaration([
    "budget_agent",
    "chatbot_agent",
    "market_watcher",
    "receipt_parser",
    "product_advisor",
    "notification_agent",
    "expense_manager",
    "forecast_agent",
    "report_agent"
])


# Function declaration for OTHER AGENTS to call the Main AI Coordinator
call_main_coordinator_declaration = {
    "name": "call_main_coordinator",
    "description": "Calls the Main AI Coordinator to handle complex tasks that require coordination between multiple agents. Use this when the user's request involves multiple aspects of their finances or requires orchestration.",
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
