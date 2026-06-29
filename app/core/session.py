import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger("voice_agent.session")

class CallSession(BaseModel):
    """
    Representation of a stateful call session.
    Manages history, active language, and pending writes (Propose-and-Commit).
    """
    session_id: str
    is_active: bool = True
    language: str = "ta"  # Default is 'ta' (Tamil), can switch to 'en'
    history: List[Dict[str, str]] = Field(default_factory=list)
    
    # Propose-and-Commit Buffer: Holds staged booking properties before DB commit
    pending_booking: Optional[Dict[str, Any]] = None

    def add_to_history(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def stage_booking(self, booking_data: Dict[str, Any]):
        """
        Stage a proposed booking in memory. Do not write to database yet.
        """
        self.pending_booking = booking_data
        logger.info(f"Staged pending booking for session {self.session_id}: {booking_data}")

    def get_staged_booking(self) -> Optional[Dict[str, Any]]:
        return self.pending_booking

    def clear_staged_booking(self):
        self.pending_booking = None
        logger.info(f"Cleared pending booking for session {self.session_id}")


class SessionManager:
    """
    Manages CallSession lifecycles.
    In development, uses an in-memory store. In production, connects to Redis.
    """
    def __init__(self):
        # In-memory session database
        self._sessions: Dict[str, CallSession] = {}
        self.redis_client = None

    async def initialize(self):
        """
        Initialize connection to Redis (or fallback to memory).
        """
        logger.info("Session manager initialized (In-memory dev mode).")
        # Prod implementation would connect to Redis client here

    async def close(self):
        """
        Clean up Redis connection pools.
        """
        logger.info("Session manager connections closed.")

    async def get_session(self, session_id: str) -> Optional[CallSession]:
        return self._sessions.get(session_id)

    async def get_or_create_session(self, session_id: str) -> CallSession:
        if session_id not in self._sessions:
            logger.info(f"Creating new stateful session: {session_id}")
            self._sessions[session_id] = CallSession(session_id=session_id)
        return self._sessions[session_id]

    async def deactivate_session(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id].is_active = False
            logger.info(f"Deactivated session: {session_id}")

    async def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Purged session: {session_id}")
            return True
        return False

# Global Singleton Session Manager
session_manager = SessionManager()
