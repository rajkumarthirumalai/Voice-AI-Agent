from typing import Optional
from app.tools.base import register_tool_with_orchestrator
from app.core.session import CallSession
from app.database.queries import check_hall_availability, get_available_halls

logger = logging.getLogger("voice_agent.tools.check_availability")

@register_tool_with_orchestrator("check_availability")
async def check_availability(session: CallSession, date: str, hall_name: Optional[str] = None) -> str:
    """
    Check availability of halls on a given date.
    If hall_name is not provided, returns all available halls on that date.
    """
    if not hall_name or hall_name.lower() in ["none", "null", "all", "any", ""]:
        logger.info(f"Checking all available halls on date {date}")
        halls = await get_available_halls(date)
        
        if not halls:
            if session.language == "ta":
                return f"{date} அன்று எந்த மண்டபங்களும் காலியாக இல்லை."
            return f"No halls are available on {date}."
            
        halls_str = ", ".join(halls)
        if session.language == "ta":
            return f"{date} அன்று காலியாக உள்ள மண்டபங்கள்: {halls_str}."
        return f"The available halls on {date} are: {halls_str}."

    logger.info(f"Checking availability for specific hall: {hall_name} on {date}")
    is_available = await check_hall_availability(hall_name, date)
    
    if session.language == "ta":
        status = "காலியாக உள்ளது" if is_available else "முன்பதிவு செய்யப்பட்டுள்ளது"
        return f"{date} அன்று {hall_name} {status}."
    else:
        status = "available" if is_available else "already booked"
        return f"{hall_name} is {status} on {date}."
