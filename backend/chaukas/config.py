"""Configuration via pydantic-settings."""

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SttProvider(str, Enum):
    AUTO = "auto"
    SARVAM = "sarvam"
    DEEPGRAM = "deepgram"
    MOCK = "mock"


class TtsProvider(str, Enum):
    AUTO = "auto"
    SARVAM = "sarvam"
    NONE = "none"


class LlmEnabled(str, Enum):
    AUTO = "auto"
    TRUE = "true"
    FALSE = "false"


class Sensitivity(str, Enum):
    STANDARD = "standard"
    HIGH = "high"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    port: int = Field(default=8787, ge=1, le=65535)
    cors_origin: str = Field(default="http://localhost:5173")

    # Providers
    stt_provider: SttProvider = Field(default=SttProvider.AUTO)
    tts_provider: TtsProvider = Field(default=TtsProvider.AUTO)
    llm_enabled: LlmEnabled = Field(default=LlmEnabled.AUTO)

    # API Keys
    sarvam_api_key: str = Field(default="")
    deepgram_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")

    # Bolna AI Telephony Integration
    bolna_api_key: str = Field(default="")
    bolna_agent_id: str = Field(default="")

    # LLM
    llm_model: str = Field(default="claude-haiku-5-5")

    # Session
    max_session_minutes: int = Field(default=30, ge=1, le=1440)

    # Logging
    log_level: str = Field(default="info")

    @validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"debug", "info", "warning", "error", "critical"}
        if v.lower() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.lower()

    def resolved_stt_provider(self) -> SttProvider:
        """Resolve 'auto' to the first available provider."""
        if self.stt_provider != SttProvider.AUTO:
            return self.stt_provider
        if self.sarvam_api_key:
            return SttProvider.SARVAM
        if self.deepgram_api_key:
            return SttProvider.DEEPGRAM
        return SttProvider.MOCK

    def resolved_tts_provider(self) -> TtsProvider:
        if self.tts_provider != TtsProvider.AUTO:
            return self.tts_provider
        if self.sarvam_api_key:
            return TtsProvider.SARVAM
        return TtsProvider.NONE

    def resolved_llm_enabled(self) -> bool:
        if self.llm_enabled == LlmEnabled.TRUE:
            return True
        if self.llm_enabled == LlmEnabled.FALSE:
            return False
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


# For backward compatibility and easy imports
settings = get_settings()