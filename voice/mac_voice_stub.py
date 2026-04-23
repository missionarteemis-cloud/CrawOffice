"""Minimal stub voice endpoint for the Mac side.

This is the first test target for the voice pipeline:
Discord -> STT on PC -> /voice/chat on Mac -> fixed text reply -> TTS on PC -> Discord playback
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


app = FastAPI(title="Craw Mac Voice Stub")


class SessionRef(BaseModel):
    guild_id: str
    channel_id: str
    user_id: str
    user_name: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_id: str = "main"


class Turn(BaseModel):
    text: str
    language: str = "it"
    source: str = "discord_voice"
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration_ms: Optional[int] = None
    confidence: Optional[float] = None


class AudioMeta(BaseModel):
    sample_rate_hz: int = 48000
    channels: int = 2
    transport: str = "pcm16"
    stt_provider: str = "faster-whisper"


class Context(BaseModel):
    recent_turns: List[Dict[str, Any]] = Field(default_factory=list)
    thread_id: Optional[str] = None
    message_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceChatRequest(BaseModel):
    session: SessionRef
    turn: Turn
    audio: AudioMeta = Field(default_factory=AudioMeta)
    context: Context = Field(default_factory=Context)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "craw-mac-voice-stub"}


@app.post("/voice/chat")
def voice_chat(req: VoiceChatRequest) -> Dict[str, Any]:
    text = f"stub attivo. ho ricevuto: {req.turn.text}"
    return {
        "ok": True,
        "reply": {
            "text": text,
            "language": req.turn.language or "it",
            "should_speak": True,
            "end_session": False,
        },
        "session": {
            "conversation_id": req.session.conversation_id,
            "agent_id": req.session.agent_id,
        },
        "timing": {
            "processing_ms": 1,
        },
        "error": None,
    }
