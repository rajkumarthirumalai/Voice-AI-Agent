from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.core.session import session_manager

router = APIRouter()

class HealthCheckResponse(BaseModel):
    status: str
    version: str

class SessionStateResponse(BaseModel):
    session_id: str
    is_active: bool
    language: str
    pending_booking: Optional[Dict[str, Any]]
    history_length: int

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Service health check endpoint.
    """
    return HealthCheckResponse(status="healthy", version="1.0.0")

@router.get("/sessions/{session_id}", response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    """
    Admin endpoint to inspect current call session state (especially for Propose-and-Commit validation).
    """
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    return SessionStateResponse(
        session_id=session.session_id,
        is_active=session.is_active,
        language=session.language,
        pending_booking=session.pending_booking,
        history_length=len(session.history)
    )

@router.delete("/sessions/{session_id}")
async def clear_session_state(session_id: str):
    """
    Admin endpoint to terminate and purge session state.
    """
    deleted = await session_manager.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": f"Session {session_id} successfully cleared"}
