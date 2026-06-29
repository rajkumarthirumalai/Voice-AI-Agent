import logging
from app.tools.base import register_tool_with_orchestrator
from app.core.session import CallSession
from app.database.queries import create_booking

logger = logging.getLogger("voice_agent.tools.commit_booking")

@register_tool_with_orchestrator("commit_booking")
async def commit_booking(session: CallSession) -> str:
    """
    Commit a previously staged booking to the database (Commit phase).
    Fails if no booking has been staged.
    """
    logger.info(f"Attempting to commit staged booking for session: {session.session_id}")
    
    staged_payload = session.get_staged_booking()
    if not staged_payload:
        if session.language == "ta":
            return "உறுதிப்படுத்த எந்த தற்காலிக முன்பதிவும் இல்லை. தயவுசெய்து முதலில் தேதியை கூறவும்."
        return "No pending booking exists to confirm. Please specify a date and hall first."
        
    # Write to database (strictly bounded DB action)
    booking_id = await create_booking(
        hall_name=staged_payload["hall_name"],
        date=staged_payload["date"],
        customer_name=staged_payload["customer_name"],
        price=staged_payload["total_price"]
    )
    
    # Clean the session buffer once committed
    session.clear_staged_booking()
    
    if session.language == "ta":
        return f"மண்டப முன்பதிவு வெற்றிகரமாக உறுதி செய்யப்பட்டது. உங்கள் முன்பதிவு எண் {booking_id}."
    else:
        return f"Booking successfully finalized! Your booking confirmation ID is {booking_id}."
