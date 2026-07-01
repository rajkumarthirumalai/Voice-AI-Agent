import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select, and_
from app.database.connection import db_manager
from app.database.models import Hall, Booking

logger = logging.getLogger("voice_agent.database.queries")

async def check_hall_availability(hall_name: str, date_str: str) -> bool:
    """
    Checks if a hall is available on a specific date.
    SQL equivalent:
    SELECT EXISTS (
        SELECT 1 FROM bookings b
        JOIN halls h ON b.hall_id = h.id
        WHERE h.name ILIKE :hall_name AND b.date = :date_str AND b.status = 'confirmed'
    );
    """
    logger.info(f"Checking availability for '{hall_name}' on '{date_str}'")
    
    # Parse date
    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        logger.error(f"Invalid date format: {date_str}")
        return False

    async with db_manager.session_maker() as session:
        # Select hall by case-insensitive name and check if a confirmed booking exists for that date
        stmt = (
            select(Booking)
            .join(Hall)
            .where(
                and_(
                    Hall.name.ilike(hall_name),
                    Booking.date == query_date,
                    Booking.status == "confirmed"
                )
            )
        )
        result = await session.execute(stmt)
        booking = result.scalars().first()
        
        # If no booking exists, the hall is available
        return booking is None


async def get_hall_pricing(hall_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetches base price and tax details for a specific hall.
    SQL equivalent:
    SELECT base_price, tax_rate FROM halls WHERE name ILIKE :hall_name;
    """
    logger.info(f"Fetching pricing details for hall: '{hall_name}'")
    
    async with db_manager.session_maker() as session:
        stmt = select(Hall).where(Hall.name.ilike(hall_name))
        result = await session.execute(stmt)
        hall = result.scalars().first()
        
        if not hall:
            logger.warning(f"Hall '{hall_name}' not found in database.")
            return None
            
        # Calculate tax base
        return {
            "base_price": float(hall.base_price),
            "tax": float(hall.base_price * (hall.tax_rate / 100))
        }


async def create_booking(hall_name: str, date_str: str, customer_name: str, price: float) -> str:
    """
    Inserts a confirmed booking into the bookings table.
    SQL equivalent:
    INSERT INTO bookings (hall_id, date, customer_name, total_price, status)
    VALUES ((SELECT id FROM halls WHERE name ILIKE :hall_name), :date_str, :customer_name, :price, 'confirmed')
    RETURNING id;
    """
    logger.info(f"Creating database transaction: booking for '{customer_name}' at '{hall_name}' on '{date_str}'")
    
    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}")

    async with db_manager.session_maker() as session:
        async with session.begin():
            # 1. Retrieve the hall ID
            stmt = select(Hall).where(Hall.name.ilike(hall_name))
            result = await session.execute(stmt)
            hall = result.scalars().first()
            
            if not hall:
                raise ValueError(f"Hall '{hall_name}' does not exist.")
            
            # 2. Instantiate and add booking model
            new_booking = Booking(
                hall_id=hall.id,
                date=query_date,
                customer_name=customer_name,
                total_price=price,
                status="confirmed"
            )
            session.add(new_booking)
            
            # Flush session to populate new_booking.id
            await session.flush()
            booking_id = str(new_booking.id)
            
            logger.info(f"Transaction complete. Staged booking committed with ID: {booking_id}")
            return f"HB-{booking_id[:6].upper()}"


async def get_available_halls(date_str: str) -> list[str]:
    """
    Returns a list of all hall names that are available (not booked) on a given date.
    """
    logger.info(f"Executing database query: Get all available halls on date '{date_str}'")
    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        logger.error(f"Invalid date format: {date_str}")
        return []

    async with db_manager.session_maker() as session:
        # Subquery to select all booked hall IDs for the date
        booked_subquery = select(Booking.hall_id).where(
            and_(
                Booking.date == query_date,
                Booking.status == "confirmed"
            )
        )
        
        # Query halls whose IDs are not in the booked subquery
        stmt = select(Hall.name).where(Hall.id.not_in(booked_subquery))
        result = await session.execute(stmt)
        return list(result.scalars().all())
