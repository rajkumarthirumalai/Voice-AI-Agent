import logging
from app.adapters.base import AbstractSTTAdapter
from app.config import settings

logger = logging.getLogger("voice_agent.adapters.stt.sarvam")

class SarvamSTTAdapter(AbstractSTTAdapter):
    """
    Adapter for Sarvam AI's Speech-to-Text API.
    Optimized for Indian languages (particularly bilingual Tamil/English speech).
    """
    def __init__(self):
        self.api_key = settings.STT_API_KEY
        self.api_url = "https://api.sarvam.ai/speech-to-text"

    async def transcribe_chunk(self, session_id: str, chunk: bytes) -> str:
        """
        Transcribes streaming audio chunks containing Tamil speech.
        """
        logger.debug(f"Piping {len(chunk)} bytes to Sarvam STT...")
        
        # In a real integration, this sends audio bytes to Sarvam AI's WebSocket/HTTP API
        # Stub implementation returns mock Tamil input
        if len(chunk) > 100:
            return "ஜூலை 5 அன்று மெயின் ஹால் காலியாக உள்ளதா?"
        return ""
