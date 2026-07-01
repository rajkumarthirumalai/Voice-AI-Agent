import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, Date, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Hall(Base):
    """
    Represents physical marriage halls or banquet halls.
    """
    __tablename__ = "halls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    base_price = Column(Numeric(10, 2), nullable=False)
    tax_rate = Column(Numeric(4, 2), nullable=False, default=18.00) # GST percentage (e.g. 18%)
    capacity = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)

    bookings = relationship("Booking", back_populates="hall", cascade="all, delete-orphan")


class Booking(Base):
    """
    Represents booking entries made on a specific hall for a unique date.
    Uses UniqueConstraint to enforce zero double-booking at the database level.
    """
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint('hall_id', 'date', name='uq_hall_date_booking'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hall_id = Column(UUID(as_uuid=True), ForeignKey("halls.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    customer_name = Column(String(150), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False, default="confirmed") # e.g. confirmed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    hall = relationship("Hall", back_populates="bookings")
