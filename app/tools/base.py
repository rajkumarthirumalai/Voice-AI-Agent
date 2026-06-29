import logging
from typing import Dict, Any, Callable
from app.core.agent import agent_orchestrator

logger = logging.getLogger("voice_agent.tools.base")

def register_tool_with_orchestrator(name: str):
    """
    Decorator to register a bounded tool with the agent orchestrator.
    Ensures that the orchestrator is aware of the tools and can execute them.
    """
    def decorator(func: Callable):
        agent_orchestrator.register_tool(name, func)
        return func
    return decorator
