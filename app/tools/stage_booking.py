import logging
from app.tools.base import register_tool_with_orchestrator
from app.core.session import CallSession
from app.database.queries import get_hall_pricing

logger = logging.getLogger("voice_agent.tools.stage_booking")

@register_tool_with_orchestrator("stage_booking")
async def stage_booking(session: CallSession, date: str, hall_name: str, customer_name: str) -> str:
    """
    Stage a booking in the stateful session buffer (Propose phase).
    DOES NOT write to the database yet.
    """
    logger.info(f"Staging booking for {hall_name} on {date}")
    
    # Calculate price to stage
    price_info = await get_hall_pricing(hall_name)
    total_price = price_info.get("base_price", 0) + price_info.get("tax", 0) if price_info else 0
    
    booking_payload = {
        "date": date,
        "hall_name": hall_name,
        "customer_name": customer_name,
        "total_price": total_price
    }
    
    # Push to Propose-and-Commit buffer inside stateful session
    session.stage_booking(booking_payload)
    
    if session.language == "ta":
        return f"{date} அன்று {hall_name} தற்காலிகமாக முன்பதிவு செய்யப்பட்டுள்ளது. கட்டணம் ₹{total_price}. இதை உறுதி செய்ய 'ஆம்' அல்லது 'உறுதி செய்' என்று கூறவும்."
    else:
        return f"Staged booking for {hall_name} on {date}. Total is ₹{total_price}. Say 'yes' or 'confirm' to finalize."
