"""Contract-first client for sending transcribed voice turns to Craw/OpenClaw.

This file intentionally starts with the JSON contract and lightweight client shape
before wiring it into the rest of the voice pipeline.

Planned flow:
  Discord audio -> STT on PC -> transcript -> CrawClient.chat_turn(...) -> text reply -> TTS on PC
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx


# ---------------------------------------------------------------------------
# Request / response contract
# ---------------------------------------------------------------------------
# Suggested HTTP endpoint on the Mac side:
#   POST /voice/chat
#
# Request JSON:
# {
#   "session": {
#     "guild_id": "1495429636111204403",
#     "channel_id": "voice-channel-id",
#     "user_id": "457986055489060877",
#     "user_name": "TrunksD",
#     "conversation_id": "discord-voice:1495429636111204403:voice-channel-id",
#     "agent_id": "main"
#   },
#   "turn": {
#     "text": "ciao craw mi senti?",
#     "language": "it",
#     "source": "discord_voice",
#     "started_at": "2026-04-23T15:40:12.120Z",
#     "ended_at": "2026-04-23T15:40:14.480Z",
#     "duration_ms": 2360,
#     "confidence": 0.91
#   },
#   "audio": {
#     "sample_rate_hz": 48000,
#     "channels": 2,
#     "transport": "pcm16",
#     "stt_provider": "faster-whisper"
#   },
#   "context": {
#     "recent_turns": [],
#     "thread_id": null,
#     "message_id": null,
#     "metadata": {}
#   }
# }
#
# Response JSON:
# {
#   "ok": true,
#   "reply": {
#     "text": "sì, ti sento. dimmi pure.",
#     "language": "it",
#     "should_speak": true,
#     "end_session": false
#   },
#   "session": {
#     "conversation_id": "discord-voice:1495429636111204403:voice-channel-id",
#     "agent_id": "main"
#   },
#   "timing": {
#     "processing_ms": 842
#   },
#   "error": null
# }


@dataclass
class VoiceSessionRef:
    guild_id: str
    channel_id: str
    user_id: str
    user_name: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_id: str = "main"


@dataclass
class VoiceTurn:
    text: str
    language: str = "it"
    source: str = "discord_voice"
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration_ms: Optional[int] = None
    confidence: Optional[float] = None


@dataclass
class VoiceAudioMeta:
    sample_rate_hz: int = 48_000
    channels: int = 2
    transport: str = "pcm16"
    stt_provider: str = "faster-whisper"


@dataclass
class VoiceContext:
    recent_turns: List[Dict[str, Any]] = field(default_factory=list)
    thread_id: Optional[str] = None
    message_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VoiceChatRequest:
    session: VoiceSessionRef
    turn: VoiceTurn
    audio: VoiceAudioMeta = field(default_factory=VoiceAudioMeta)
    context: VoiceContext = field(default_factory=VoiceContext)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session": {
                "guild_id": self.session.guild_id,
                "channel_id": self.session.channel_id,
                "user_id": self.session.user_id,
                "user_name": self.session.user_name,
                "conversation_id": self.session.conversation_id,
                "agent_id": self.session.agent_id,
            },
            "turn": {
                "text": self.turn.text,
                "language": self.turn.language,
                "source": self.turn.source,
                "started_at": self.turn.started_at,
                "ended_at": self.turn.ended_at,
                "duration_ms": self.turn.duration_ms,
                "confidence": self.turn.confidence,
            },
            "audio": {
                "sample_rate_hz": self.audio.sample_rate_hz,
                "channels": self.audio.channels,
                "transport": self.audio.transport,
                "stt_provider": self.audio.stt_provider,
            },
            "context": {
                "recent_turns": self.context.recent_turns,
                "thread_id": self.context.thread_id,
                "message_id": self.context.message_id,
                "metadata": self.context.metadata,
            },
        }


@dataclass
class VoiceReply:
    text: str
    language: str = "it"
    should_speak: bool = True
    end_session: bool = False


@dataclass
class VoiceChatError:
    code: str
    message: str


@dataclass
class VoiceChatResponse:
    ok: bool
    reply: Optional[VoiceReply] = None
    session: Dict[str, Any] = field(default_factory=dict)
    timing: Dict[str, Any] = field(default_factory=dict)
    error: Optional[VoiceChatError] = None


class CrawClient:
    """Thin contract-first client for the Mac-side /voice/chat endpoint."""

    def __init__(self, base_url: str, timeout_seconds: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def build_chat_request(
        self,
        *,
        guild_id: str,
        channel_id: str,
        user_id: str,
        user_name: Optional[str],
        text: str,
        conversation_id: Optional[str] = None,
        language: str = "it",
        confidence: Optional[float] = None,
    ) -> VoiceChatRequest:
        if not conversation_id:
            conversation_id = f"discord-voice:{guild_id}:{channel_id}"
        return VoiceChatRequest(
            session=VoiceSessionRef(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                user_name=user_name,
                conversation_id=conversation_id,
            ),
            turn=VoiceTurn(
                text=text,
                language=language,
                confidence=confidence,
            ),
        )

    def chat_turn(self, request: VoiceChatRequest) -> VoiceChatResponse:
        payload = request.to_dict()
        response = httpx.post(
            f"{self.base_url}/voice/chat",
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()

        reply = data.get("reply")
        error = data.get("error")
        return VoiceChatResponse(
            ok=bool(data.get("ok")),
            reply=VoiceReply(**reply) if reply else None,
            session=data.get("session") or {},
            timing=data.get("timing") or {},
            error=VoiceChatError(**error) if error else None,
        )
