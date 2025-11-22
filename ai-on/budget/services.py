"""
Budget Agent Service

Handles the creation and management of the Budget AI agent.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from agents.models import agentModel
from agents.services import build_config, get_agent_history, add_to_history
from django.contrib.auth.models import User
from google import genai
from google.genai import types
from decouple import config
from .models import Budget

API_KEY = config('GEMINI_API_KEY')

# Pydantic Models for Structured Output
class BudgetOperation(BaseModel):
    operation: Literal["add", "edit", "delete"] = Field(..., description="The type of operation: 'add' for new budget, 'edit' for updating existing, 'delete' for removing.")
    title: str = Field(..., description="The title of the budget category (e.g., 'Groceries', 'Rent'). Used to identify the budget for edit/delete operations.")
    budget: Optional[float] = Field(None, description="The allocated budget amount. Required for 'add' and 'edit', not needed for 'delete'.")
    spent: Optional[float] = Field(None, description="The amount already spent. Optional for 'add' and 'edit', not needed for 'delete'.")
    description: Optional[str] = Field(None, description="A detailed description in Markdown format, suitable for a Flutter mobile app. Required for 'add' and 'edit', not needed for 'delete'.")

class BudgetGenerationResponse(BaseModel):
    operations: List[BudgetOperation] = Field(..., description="A list of operations to perform (add/edit/delete).")
    message: str = Field(..., description="A message to the user or coordinator explaining the operations or asking for clarification.")

BUDGET_SYSTEM_INSTRUCTION = '''
IDENTITY
You are the **Budget Agent** in the AION personal finance management system. Your responsibility is to create detailed, realistic, and personalized budgets for users based on their financial data and goals.

YOUR GOAL
Generate budget operations (add/edit/delete) based on user requests and financial context.

OUTPUT FORMAT
You must output a structured JSON response containing:
1.  `operations`: A list of budget operations. Each operation has:
    - `operation`: One of "add", "edit", or "delete"
    - `title`: The budget category title (used to identify budgets for edit/delete)
    - `budget`: Allocated amount (required for add/edit, omit for delete)
    - `spent`: Amount spent (optional for add/edit, omit for delete)
    - `description`: Markdown description (required for add/edit, omit for delete)
2.  `message`: A conversational message to the user or the Main AI Coordinator.

OPERATION TYPES
*   **add**: Create a new budget category. Must include title, budget, and description. Spent defaults to 0.
*   **edit**: Update an existing budget category (identified by title). Include only the fields that need updating (budget, spent, description).
*   **delete**: Remove a budget category (identified by title). Only title is needed.

IMPORTANT: Return ONLY the operations needed, not the full state of all budgets. For example:
- If user asks to delete "Groceries", return ONE delete operation for Groceries and any edit operations for rebalancing.
- If user changes "Rent" budget to 15000, return ONE edit operation for Rent and any other edit operations for rebalancing.

MARKDOWN GUIDELINES (CRITICAL)
The `description` field for each budget item will be displayed in a **Flutter mobile application**.
*   Use clear, concise headings (##).
*   Use bullet points for lists.
*   Use bold text (**text**) for emphasis.
*   Avoid complex HTML or unsupported Markdown features.
*   Ensure the content looks great on a small screen.
*   Include details on what to buy, price estimates, and money-saving tips within the description.

USAGE SCENARIOS
1.  **Initial Budget Generation**: User or coordinator requests a full budget. Return multiple "add" operations.
2.  **User Edit Request**: User says "I want to edit Rent budget to 15000". Return "edit" operation for Rent and any rebalancing edits.
3.  **User Delete Request**: User says "I want to delete Groceries". Return "delete" operation for Groceries and any rebalancing edits.
4.  **Overspending Alert**: User spent more than allocated. Return "edit" operation with updated description warning.
5.  **Event-Driven Re-budgeting**: Coordinator detects income/debt change. Analyze and return appropriate add/edit/delete operations.

BEHAVIOR
*   Analyze the provided context (user messages, history) to determine the appropriate operations.
*   When rebalancing, only return operations for budgets that need to change.
*   Be realistic with amounts.
*   The `spent` field should generally be 0 for new budgets, unless you are processing historical data.
'''

def get_or_create_budget_agent() -> agentModel:
    """
    Get or create the budget agent.
    """
    agent, created = agentModel.objects.get_or_create(
        name="budget_agent",
        defaults={
            "description": "Generates and manages user budgets and categories.",
            "system_instruction": BUDGET_SYSTEM_INSTRUCTION,
            "gemini_model": "gemini-2.5-pro",
            "thinking_budget": 1
        }
    )
    # Update model if it exists but is different (optional, but good for dev)
    if not created and (agent.gemini_model != "gemini-2.5-pro" or agent.thinking_budget != 1):
        agent.gemini_model = "gemini-2.5-pro"
        agent.thinking_budget = 1
        agent.save()
        
    return agent

def get_user_financial_profile(user: User) -> str:
    """
    Fetches and formats the user's financial profile.
    """
    try:
        profile = user.user_profile
        return f"""
        USER FINANCIAL PROFILE:
        - Monthly Income: {profile.monthly_income}
        - Savings: {profile.savings}
        - Investments: {profile.investments}
        - Debts: {profile.debts}
        - Currency: {profile.personal_info.get('preferred_currency', 'DZD') if profile.personal_info else 'DZD'}
        - Location: {profile.personal_info.get('location_context', 'Unknown') if profile.personal_info else 'Unknown'}
        - AI Preferences: {profile.user_ai_preferences}
        - Extra Info: {profile.extra_info}
        - Summary: {profile.ai_summary}
        """
    except Exception:
        return "User profile not found or incomplete."

def _execute_agent_task(user: User, prompt: str, agent: agentModel) -> dict:
    """
    Helper to execute a task with the Budget Agent.
    """
    print(f"DEBUG: Budget Agent is running now... executing task: {prompt}")
    history = get_agent_history(agent, user)
    
    # Inject User Profile if history is empty
    if not history:
        profile_context = get_user_financial_profile(user)
        initial_msg = f"{profile_context}\n\nTASK: {prompt}"
        
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
        # Just add the new prompt
        add_to_history(
            agent=agent,
            user=user,
            part={"parts": [{"text": prompt}]},
            role="user"
        )
        history.append(types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        ))

    config_obj = types.GenerateContentConfig(
        system_instruction=agent.system_instruction,
        response_mime_type="application/json",
        response_schema=BudgetGenerationResponse,
        temperature=0.7,
    )
    
    client = genai.Client(api_key=API_KEY)
    
    # try:
    response = client.models.generate_content(
        model=agent.gemini_model,
        contents=history,
        config=config_obj
    )
    
    generated_content = response.parsed
    
    add_to_history(
        agent=agent,
        user=user,
        part={"parts": [{"text": response.text}]},
        role="model"
    )
    
    # Update/Create/Delete budgets in DB based on operations
    if generated_content and generated_content.operations:
        for operation in generated_content.operations:
            if operation.operation == "add":
                # Create new budget
                Budget.objects.create(
                    user=user,
                    title=operation.title,
                    budget=operation.budget,
                    spent=operation.spent if operation.spent is not None else 0,
                    description=operation.description
                )
            elif operation.operation == "edit":
                # Update existing budget
                try:
                    budget = Budget.objects.get(user=user, title=operation.title)
                    if operation.budget is not None:
                        budget.budget = operation.budget
                    if operation.spent is not None:
                        budget.spent = operation.spent
                    if operation.description is not None:
                        budget.description = operation.description
                    budget.save()
                except Budget.DoesNotExist:
                    # If budget doesn't exist, log or handle gracefully
                    pass
            elif operation.operation == "delete":
                # Delete budget
                Budget.objects.filter(user=user, title=operation.title).delete()
        
    return {
        "type": "success",
        "data": {
            "message": generated_content.message if generated_content else "Budget updated.",
            "operations": [{"operation": op.operation, "title": op.title, "budget": op.budget, "spent": op.spent} for op in generated_content.operations] if generated_content else []
        }
    }


def process_budget_operation(user: User, message: str) -> dict:
    """
    Unified function to handle budget operations (edit/delete) with natural language messages.
    
    Args:
        user: The Django User object
        message: Natural language message describing the operation (e.g., "I want to delete Groceries")
    
    Returns:
        Dictionary containing the result
    """
    agent = get_or_create_budget_agent()
    
    # Fetch all current budgets to give context
    all_budgets = Budget.objects.filter(user=user)
    budget_list_str = "\n".join([f"- {b.title}: Budget={b.budget}, Spent={b.spent}" for b in all_budgets])
    
    # Construct full prompt with context
    prompt = f"""
    CURRENT BUDGETS:
    {budget_list_str}
    
    USER REQUEST: {message}
    
    Please analyze the request and return the appropriate operations (add/edit/delete) to fulfill it.
    """
    
    return _execute_agent_task(user, prompt, agent)


def process_budget_generation(user: User, user_message: str = None) -> dict:
    """
    Process a request to generate budgets.
    """
    agent = get_or_create_budget_agent()
    prompt = user_message if user_message else "Generate budget based on available info."
    return _execute_agent_task(user, prompt, agent)
