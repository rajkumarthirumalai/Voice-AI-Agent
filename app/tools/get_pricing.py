import logging
from app.tools.base import register_tool_with_orchestrator
from app.core.session import CallSession
from app.database.queries import get_hall_pricing

logger = logging.getLogger("voice_agent.tools.get_pricing")

@register_tool_with_orchestrator("get_pricing")
async def get_pricing(session: CallSession, hall_name: str) -> str:
    """
    Retrieve pricing details for a given hall.
    """
    logger.info(f"Retrieving pricing for {hall_name}")
    
    # Strictly bounded DB query
    price_info = await get_hall_pricing(hall_name)
    
    if not price_info:
        if session.language == "ta":
            return f"மன்னிக்கவும், {hall_name} கட்டண விவரங்கள் கிடைக்கவில்லை."
        return f"Sorry, pricing for {hall_name} is not available."
        
    base_price = price_info.get("base_price", 0)
    tax = price_info.get("tax", 0)
    total = base_price + tax
    
    if session.language == "ta":
        return f"{hall_name} கட்டணம்: அடிப்படை ₹{base_price}, மொத்த தொகை ₹{total}."
    else:
        return f"{hall_name} pricing: Base rate ₹{base_price}, Total ₹{total} including taxes."
