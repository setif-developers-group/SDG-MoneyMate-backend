"""
Advisor Agent Tools

These are the function tools for integrating the Advisor Agent with the Chatbot.
"""

from django.contrib.auth.models import User


def call_advisor(user: User, message: str) -> dict:
    """
    Call the Advisor Agent for product recommendations and purchase guidance.
    
    This function allows the chatbot to delegate product advice requests
    to the Advisor Agent.
    
    Args:
        user: The Django User object
        message: The message/request to send to the Advisor Agent
        
    Returns:
        Dictionary with the advisor's response
    """
    from advisor.services import (
        process_product_recommendation,
        process_purchase_analysis,
        process_product_comparison
    )
    
    # Determine which service to call based on message content
    # For simplicity, we'll use a unified approach and let the AI handle it
    # You could add more sophisticated routing logic here
    
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['compare', 'versus', 'vs', 'or', 'between']):
        return process_product_comparison(user, message)
    elif any(word in message_lower for word in ['should i buy', 'can i afford', 'is it worth', 'good idea']):
        return process_purchase_analysis(user, message)
    else:
        # Default to recommendation
        return process_product_recommendation(user, message)


# ============================================================================
# FUNCTION DECLARATION FOR GEMINI API
# ============================================================================

call_advisor_declaration = {
    "name": "call_advisor",
    "description": "Calls the Advisor Agent to provide smart product recommendations and purchase guidance. Use this when the user asks about buying products, needs shopping advice, wants product comparisons, or asks if they can afford something. Examples: 'Should I buy this laptop?', 'Recommend a phone under 30000', 'Compare iPhone vs Samsung', 'Can I afford a new TV?'",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The user's request for product advice, recommendations, or purchase analysis. Pass the user's message directly."
            }
        },
        "required": ["message"]
    }
}
