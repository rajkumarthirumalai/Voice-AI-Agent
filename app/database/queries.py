import logging
import uuid
from typing import Dict, Any, Optional
from app.database.connection import db_manager

logger = logging.getLogger("voice_agent.database.queries")

async def check_hall_availability(hall_name: str, date: str) -> bool:
    """
    Query the database to check if the specified hall is available on the given date.
    """
    logger.info(f"Executing database query: Check availability for '{hall_name}' on date '{date}'")
    
    # In production:
    # async with db_manager.session_maker() as session:
    #     result = await session.execute(...)
    #     return result.scalar() is None
    
    # Mocking behavior (available on odd days for test logic)
    try:
        day = int(date.split("-")[-1])
        return day % 2 != 0
    except Exception:
        return True


async def get_hall_pricing(hall_name: str) -> Optional[Dict[str, Any]]:
    """
    Query the database to retrieve tariff prices and taxes for a hall.
    """
    logger.info(f"Executing database query: Get pricing details for '{hall_name}'")
    
    # Mock database records
    halls_db = {
        "main hall": {"base_price": 50000.0, "tax": 9000.0},
        "mini hall": {"base_price": 25000.0, "tax": 4500.0},
        "party hall": {"base_price": 15000.0, "tax": 2700.0}
    }
    
    return halls_db.get(hall_name.lower(), {"base_price": 30000.0, "tax": 5400.0})


async def create_booking(hall_name: str, date: str, customer_name: str, price: float) -> str:
    """
    Strictly bounded write operation. Inserts a new booking record into the database.
    """
    logger.info(f"Executing database transaction: Create booking for {customer_name} at {hall_name} on {date}")
    
    # In production:
    # async with db_manager.session_maker() as session:
    #     async with session.begin():
    #         booking = Booking(hall_name=hall_name, date=date, customer_name=customer_name, price=price)
    #         session.add(booking)
    #     return booking.id
        
    # Generate mock booking confirmation code
    booking_id = f"HB-{uuid.uuid4().hex[:6].upper()}"
    return booking_id
