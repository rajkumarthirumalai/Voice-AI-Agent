import logging
import httpx
from app.adapters.base import AbstractSTTAdapter
from app.config import settings

logger = logging.getLogger("voice_agent.adapters.stt.deepgram")

class DeepgramSTTAdapter(AbstractSTTAdapter):
    """
    Adapter for Deepgram's Speech-to-Text API.
    Handles streaming transcription.
    """
    def __init__(self):
        self.api_key = settings.STT_API_KEY
        self.api_url = "https://api.deepgram.com/v1/listen"

    async def transcribe_chunk(self, session_id: str, chunk: bytes) -> str:
        """
        Sends raw audio bytes to Deepgram STT and retrieves transcription.
        In a streaming scenario, this would typically write to a persistent WebSocket.
        """
        # Mock request demonstrating interface flow
        logger.debug(f"Piping {len(chunk)} bytes to Deepgram STT...")
        
        # Real integration would use httpx.AsyncClient or websockets to connect to Deepgram
        # For stubbing, we return mock values
        if len(chunk) > 100:
            return "is Main Hall available on July 5th?"
        return ""
