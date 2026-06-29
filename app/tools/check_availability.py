import logging
from app.tools.base import register_tool_with_orchestrator
from app.core.session import CallSession
from app.database.queries import check_hall_availability

logger = logging.getLogger("voice_agent.tools.check_availability")

@register_tool_with_orchestrator("check_availability")
async def check_availability(session: CallSession, date: str, hall_name: str) -> str:
    """
    Check if a specific hall is available for booking on a given date.
    LLM calls this when user asks about availability.
    """
    logger.info(f"Checking availability for {hall_name} on {date}")
    
    # Strictly bounded DB query access (no raw SQL execution by LLM)
    is_available = await check_hall_availability(hall_name, date)
    
    if session.language == "ta":
        status = "காலியாக உள்ளது" if is_available else "முன்பதிவு செய்யப்பட்டுள்ளது"
        return f"{date} அன்று {hall_name} {status}."
    else:
        status = "available" if is_available else "already booked"
        return f"{hall_name} is {status} on {date}."
