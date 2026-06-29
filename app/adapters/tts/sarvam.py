import logging
from typing import AsyncGenerator
from app.adapters.base import AbstractTTSAdapter
from app.config import settings

logger = logging.getLogger("voice_agent.adapters.tts.sarvam")

class SarvamTTSAdapter(AbstractTTSAdapter):
    """
    Adapter for Sarvam AI's Text-to-Speech API.
    Provides natural-sounding speech output for Tamil (e.g. using 'arvind' voice).
    """
    def __init__(self):
        self.api_key = settings.TTS_API_KEY
        self.api_url = "https://api.sarvam.ai/text-to-speech"

    async def synthesize_stream(self, text: str, language: str) -> AsyncGenerator[bytes, None]:
        """
        Calls Sarvam's text-to-speech endpoint, optimized for Indian languages,
        and yields synthesized audio streams.
        """
        logger.info(f"Synthesizing bilingual text to speech via Sarvam: '{text}' in language: {language}")
        
        # In a real integration, this sends an HTTP request to Sarvam and streams back the audio bytes.
        # Yield mock binary data representing synthesized Tamil audio packets
        yield b"\x10\x11\x12\x13"
        yield b"\x14\x15\x16\x17"
