"""
Agent Service Layer
Handles all business logic for agents, including:
- Tool/function management
- Gemini configuration building
- Function execution
- Agent registry management

This separation avoids circular dependencies and keeps models.py clean.
"""

from google.genai import types
from .models import agentModel, ConversationHistory
from django.contrib.auth.models import User


# Global registry to store function declarations and implementations per agent
# Structure: {agent_id: {func_name: {'declaration': dict, 'function': callable}}}
AGENT_FUNCTION_REGISTRY = {}


def register_agent_function(agent_id: int, func_name: str, function_declaration: dict, function: callable):
    """
    Register a function for a specific agent.
    
    Args:
        agent_id: The ID of the agent
        func_name: Name of the function
        function_declaration: Gemini function declaration dict
        function: The actual callable function
    """
    if agent_id not in AGENT_FUNCTION_REGISTRY:
        AGENT_FUNCTION_REGISTRY[agent_id] = {}
    
    if func_name not in AGENT_FUNCTION_REGISTRY[agent_id]:
        AGENT_FUNCTION_REGISTRY[agent_id][func_name] = {
            'declaration': function_declaration,
            'function': function
        }


def get_agent_functions(agent_id: int) -> dict:
    """
    Get all registered functions for an agent.
    
    Args:
        agent_id: The ID of the agent
        
    Returns:
        Dictionary of functions for this agent
    """
    return AGENT_FUNCTION_REGISTRY.get(agent_id, {})


def build_tools(agent: agentModel) -> types.Tool | None:
    """
    Build Gemini Tool object from registered functions for an agent.
    
    Args:
        agent: The agent model instance
        
    Returns:
        types.Tool object or None if no functions registered
    """
    functions = get_agent_functions(agent.id)
    
    if len(functions) == 0:
        return None
    
    tools = []
    for func_entry in functions.values():
        tools.append(func_entry['declaration'])
    
    return types.Tool(function_declarations=tools)


def build_config(agent: agentModel) -> types.GenerateContentConfig:
    """
    Build Gemini configuration for an agent.
    
    Args:
        agent: The agent model instance
        
    Returns:
        GenerateContentConfig object ready for Gemini API
    """
    config_args = {
        "system_instruction": agent.system_instruction,
    }
    
    if agent.thinking_budget > 0:
        config_args["thinking_config"] = types.ThinkingConfig(thinking_budget=agent.thinking_budget)
        
    config = types.GenerateContentConfig(**config_args)
    
    tools = build_tools(agent)
    if tools:
        config.tools = [tools]
        config.tool_config = types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="AUTO"
            )
        )
    
    return config


def execute_function(agent: agentModel, func_name: str, args: dict):
    """
    Execute a registered function for an agent.
    
    Args:
        agent: The agent model instance
        func_name: Name of the function to execute
        args: Arguments to pass to the function
        
    Returns:
        Result of the function execution
        
    Raises:
        ValueError: If function not found for this agent
    """
    functions = get_agent_functions(agent.id)
    func_entry = functions.get(func_name)
    
    if func_entry:
        return func_entry['function'](**args)
    else:
        raise ValueError(f"Function '{func_name}' not found in agent '{agent.name}'.")


def get_agent_history(agent: agentModel, user: User) -> list[types.Content]:
    """
    Get conversation history for an agent and user.
    
    Args:
        agent: The agent model instance
        user: The user
        
    Returns:
        List of Content objects for Gemini API
    """
    contents = ConversationHistory.objects.filter(user=user, agent=agent).order_by('timestamp')
    content = []
    
    for m in contents:
        content.append(
            types.Content(
                role=m.role,
                parts=m.content_data.get('parts', []),
            ),
        )
    
    return content


def add_to_history(agent: agentModel, user: User, part: dict, role: str):
    """
    Add a message to conversation history.
    
    Args:
        agent: The agent model instance
        user: The user
        part: Content data to store
        role: 'user' or 'model'
    """
    ConversationHistory.objects.create(
        user=user,
        agent=agent,
        role=role,
        content_data=part
    )


def clear_agent_history(agent: agentModel, user: User):
    """
    Clear conversation history for an agent and user.
    
    Args:
        agent: The agent model instance
        user: The user
    """
    ConversationHistory.objects.filter(user=user, agent=agent).delete()



def clear_agent_functions(agent_id: int):
    """
    Clear all registered functions for an agent.
    Useful for testing or reinitialization.
    
    Args:
        agent_id: The ID of the agent
    """
    if agent_id in AGENT_FUNCTION_REGISTRY:
        del AGENT_FUNCTION_REGISTRY[agent_id]
