import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Environment
    ENV: str = Field(default="development", description="Application environment (development/production)")
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/hall_booking",
        description="Asyncpg database connection string"
    )
    
    # Redis Session Storage
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for stateful session storage"
    )
    
    # LLM Settings
    LLM_API_KEY: str = Field(default="mock_llm_key", description="API key for LLM gateway provider")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="API key for Gemini Developer API")
    LLM_MODEL: str = Field(default="gemini-2.5-flash", description="Model name to use for orchestrator")
    LLM_TEMPERATURE: float = Field(default=0.0, description="Temperature parameter for system guardrails")
    
    # STT Provider Settings
    STT_PROVIDER: str = Field(default="deepgram", description="Primary STT provider (deepgram/sarvam)")
    STT_API_KEY: str = Field(default="mock_stt_key", description="API key for STT")
    
    # TTS Provider Settings
    TTS_PROVIDER: str = Field(default="deepgram", description="Primary TTS provider (deepgram/sarvam)")
    TTS_API_KEY: str = Field(default="mock_tts_key", description="API key for TTS")
    
    # System Prompts & Fallbacks
    DEFAULT_LANGUAGE: str = Field(default="ta", description="Default fallback language ('ta' for Tamil, 'en' for English)")

settings = Settings()
# Force process reload to pick up new .env variables

