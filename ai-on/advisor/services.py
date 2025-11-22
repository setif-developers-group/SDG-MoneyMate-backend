"""
Advisor Agent Service

Handles product recommendations, purchase analysis, and product comparisons
with budget-aware AI guidance.
"""

from django.contrib.auth.models import User
from agents.models import agentModel
from budget.models import Budget
from expense.models import Expense
from .models import AdvisorSession
from google import genai
from google.genai import types
from decouple import config
from decimal import Decimal

API_KEY = config('GEMINI_API_KEY')

ADVISOR_SYSTEM_INSTRUCTION = """
IDENTITY
You are the **Advisor Agent** in the AION personal finance management system. Your role is to provide smart product recommendations and purchase guidance.

YOUR TASKS
1. **Product Recommendations**: Suggest products based on user needs and budget constraints
2. **Purchase Analysis**: Analyze if a specific purchase fits the user's financial situation
3. **Product Comparison**: Compare multiple products and recommend the best option considering budget

CRITICAL RULES
- ALWAYS consider the user's budget constraints
- If a purchase would cause overspending, suggest budget-friendly alternatives
- Analyze the user's spending patterns from their expense history
- Provide clear, actionable advice in Markdown format
- Be honest about financial implications
- Prioritize the user's financial health over making a purchase

OUTPUT FORMAT
- Use Markdown formatting with headers, bullet points, and emphasis
- Structure responses clearly with sections like "Analysis", "Recommendation", "Alternatives"
- Include specific price points and budget impact
- Provide reasoning for recommendations

TONE
- Helpful and supportive
- Honest about financial realities
- Encouraging of smart financial decisions
- Professional but friendly
"""

def get_or_create_advisor_agent() -> agentModel:
    """
    Get or create the advisor agent.
    """
    agent, created = agentModel.objects.get_or_create(
        name="advisor_agent",
        defaults={
            "description": "Agent that provides smart product recommendations and purchase guidance",
            "system_instruction": ADVISOR_SYSTEM_INSTRUCTION,
            "gemini_model": "gemini-2.5-flash",
            "thinking_budget": 0
        }
    )
    
    # Update if needed
    if not created and (agent.gemini_model != "gemini-2.5-flash" or agent.system_instruction != ADVISOR_SYSTEM_INSTRUCTION):
        agent.gemini_model = "gemini-2.5-flash"
        agent.system_instruction = ADVISOR_SYSTEM_INSTRUCTION
        agent.save()
    
    return agent


def _get_user_financial_context(user: User) -> str:
    """
    Build financial context for the AI including budget and expense data.
    """
    try:
        profile = user.user_profile
        budgets = Budget.objects.filter(user=user)
        recent_expenses = Expense.objects.filter(user=user).order_by('-date')[:10]
        
        # Calculate total budget and spending
        total_budget = sum(b.budget for b in budgets)
        total_spent = sum(b.spent for b in budgets)
        remaining = total_budget - total_spent
        
        budget_summary = "\n".join([
            f"- {b.title}: Budget {b.budget} DZD, Spent {b.spent} DZD, Remaining {b.budget - b.spent} DZD"
            for b in budgets
        ])
        
        expense_summary = "\n".join([
            f"- {e.date.date()}: {e.product_name} ({e.amount} DZD) - {e.budget.title if e.budget else 'Uncategorized'}"
            for e in recent_expenses
        ])
        
        context = f"""
USER FINANCIAL PROFILE:
- Monthly Income: {profile.monthly_income} DZD
- Savings: {profile.savings} DZD
- Investments: {profile.investments} DZD
- Debts: {profile.debts} DZD

BUDGET OVERVIEW:
Total Budget: {total_budget} DZD
Total Spent: {total_spent} DZD
Remaining: {remaining} DZD

BUDGET CATEGORIES:
{budget_summary if budget_summary else "No budgets set"}

RECENT EXPENSES (Last 10):
{expense_summary if expense_summary else "No expenses recorded"}

IMPORTANT: Consider these financial constraints when providing advice. If a purchase would cause overspending or financial strain, recommend alternatives or suggest waiting.
"""
        return context
        
    except Exception as e:
        print(f"DEBUG: Error getting financial context: {str(e)}")
        return "USER FINANCIAL PROFILE: Not available. Provide general advice."


def process_product_recommendation(user: User, message: str) -> dict:
    """
    Generate product recommendations based on user needs and budget.
    
    Args:
        user: The Django User object
        message: User's request for product recommendations
        
    Returns:
        Dictionary with AI-generated advice
    """
    print(f"DEBUG: Advisor Agent (Recommend) is running now... processing message: {message}")
    agent = get_or_create_advisor_agent()
    
    # Build context
    financial_context = _get_user_financial_context(user)
    
    prompt = f"""
{financial_context}

USER REQUEST: {message}

TASK: Provide product recommendations that fit the user's budget and financial situation. If the request is vague, ask clarifying questions or provide a range of options at different price points.
"""
    
    try:
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model=agent.gemini_model,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                system_instruction=agent.system_instruction
            )
        )
        
        advice = response.text
        
        # Save session
        session = AdvisorSession.objects.create(
            user=user,
            query_type='recommend',
            user_query=message,
            ai_response=advice
        )
        
        return {
            "type": "success",
            "data": {
                "advice": advice,
                "session_id": session.id
            }
        }
        
    except Exception as e:
        print(f"DEBUG: Error in process_product_recommendation: {str(e)}")
        return {
            "type": "error",
            "data": {"error": f"Failed to generate recommendation: {str(e)}"}
        }


def process_purchase_analysis(user: User, message: str) -> dict:
    """
    Analyze if a specific purchase fits the user's budget.
    
    Args:
        user: The Django User object
        message: User's purchase analysis request
        
    Returns:
        Dictionary with AI-generated analysis
    """
    print(f"DEBUG: Advisor Agent (Analyze) is running now... processing message: {message}")
    agent = get_or_create_advisor_agent()
    
    # Build context
    financial_context = _get_user_financial_context(user)
    
    prompt = f"""
{financial_context}

USER REQUEST: {message}

TASK: Analyze if this purchase is financially wise for the user. Consider:
1. Does it fit within their budget?
2. Which budget category would it come from?
3. Would it cause overspending?
4. Are there more affordable alternatives?
5. Is this a need or a want?

Provide a clear recommendation: "Go ahead", "Consider alternatives", or "Not recommended right now" with detailed reasoning.
"""
    
    try:
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model=agent.gemini_model,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                system_instruction=agent.system_instruction
            )
        )
        
        advice = response.text
        
        # Save session
        session = AdvisorSession.objects.create(
            user=user,
            query_type='analyze',
            user_query=message,
            ai_response=advice
        )
        
        return {
            "type": "success",
            "data": {
                "advice": advice,
                "session_id": session.id
            }
        }
        
    except Exception as e:
        print(f"DEBUG: Error in process_purchase_analysis: {str(e)}")
        return {
            "type": "error",
            "data": {"error": f"Failed to analyze purchase: {str(e)}"}
        }


def process_product_comparison(user: User, message: str) -> dict:
    """
    Compare multiple products and recommend the best option.
    
    Args:
        user: The Django User object
        message: User's product comparison request
        
    Returns:
        Dictionary with AI-generated comparison
    """
    print(f"DEBUG: Advisor Agent (Compare) is running now... processing message: {message}")
    agent = get_or_create_advisor_agent()
    
    # Build context
    financial_context = _get_user_financial_context(user)
    
    prompt = f"""
{financial_context}

USER REQUEST: {message}

TASK: Compare the products mentioned and recommend the best option considering:
1. Price and value for money
2. User's budget constraints
3. Features and quality
4. Long-term value
5. Financial impact

Provide a structured comparison with pros/cons and a clear recommendation.
"""
    
    try:
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model=agent.gemini_model,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                system_instruction=agent.system_instruction
            )
        )
        
        advice = response.text
        
        # Save session
        session = AdvisorSession.objects.create(
            user=user,
            query_type='compare',
            user_query=message,
            ai_response=advice
        )
        
        return {
            "type": "success",
            "data": {
                "advice": advice,
                "session_id": session.id
            }
        }
        
    except Exception as e:
        print(f"DEBUG: Error in process_product_comparison: {str(e)}")
        return {
            "type": "error",
            "data": {"error": f"Failed to compare products: {str(e)}"}
        }
