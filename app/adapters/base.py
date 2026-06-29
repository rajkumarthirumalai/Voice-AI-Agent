from abc import ABC, abstractmethod
from typing import AsyncGenerator
from app.config import settings

class AbstractSTTAdapter(ABC):
    """
    Abstract interface for Speech-to-Text translation.
    Converts real-time streaming audio bytes into text.
    """
    @abstractmethod
    async def transcribe_chunk(self, session_id: str, chunk: bytes) -> str:
        """
        Processes a single raw audio chunk and returns the transcribed text.
        """
        pass


class AbstractTTSAdapter(ABC):
    """
    Abstract interface for Text-to-Speech synthesis.
    Converts agent response text into a stream of audio bytes.
    """
    @abstractmethod
    async def synthesize_stream(self, text: str, language: str) -> AsyncGenerator[bytes, None]:
        """
        Synthesizes text and yields audio bytes sequentially.
        """
        yield b""


def get_stt_adapter() -> AbstractSTTAdapter:
    """
    Dependency injector choosing the STT adapter based on settings.
    """
    provider = settings.STT_PROVIDER.lower()
    if provider == "sarvam":
        from app.adapters.stt.sarvam import SarvamSTTAdapter
        return SarvamSTTAdapter()
    else:
        from app.adapters.stt.deepgram import DeepgramSTTAdapter
        return DeepgramSTTAdapter()


def get_tts_adapter() -> AbstractTTSAdapter:
    """
    Dependency injector choosing the TTS adapter based on settings.
    """
    provider = settings.TTS_PROVIDER.lower()
    if provider == "sarvam":
        from app.adapters.tts.sarvam import SarvamTTSAdapter
        return SarvamTTSAdapter()
    else:
        from app.adapters.tts.deepgram import DeepgramTTSAdapter
        return DeepgramTTSAdapter()
