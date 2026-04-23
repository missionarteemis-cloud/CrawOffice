"""Discord voice receive sink.

Receives raw PCM frames from discord.py voice receive, buffers per user, normalizes
format toward the STT path, and emits chunks suitable for transcription.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional
import audioop

import discord


TranscriptionCallback = Callable[[discord.User, bytes], None]


@dataclass
class UserAudioBuffer:
    user_id: int
    pcm16_mono_16khz: bytearray = field(default_factory=bytearray)
    frame_count: int = 0


class CrawAudioSink(discord.AudioSink):
    """Buffers incoming Discord voice audio per user.

    Input from discord.py receive path:
    - data.pcm -> signed 16-bit PCM
    - stereo
    - 48kHz

    Current sink behavior:
    - downmix stereo to mono
    - resample 48kHz -> 16kHz
    - keep PCM16LE buffers ready for PcTranscriber
    - emit a chunk callback when threshold is reached
    """

    def __init__(
        self,
        *,
        on_chunk: Optional[TranscriptionCallback] = None,
        chunk_duration_ms: int = 1500,
    ):
        super().__init__()
        self.on_chunk = on_chunk
        self.chunk_duration_ms = chunk_duration_ms
        self._buffers: Dict[int, UserAudioBuffer] = {}
        self._resample_state: Dict[int, tuple] = {}
        self._target_chunk_bytes = int(16_000 * 2 * (chunk_duration_ms / 1000.0))

    def wants_opus(self) -> bool:
        return False

    def write(self, user: discord.User, data: discord.VoiceData):
        if user is None or data is None or not getattr(data, "pcm", None):
            return

        pcm_48k_stereo = data.pcm
        pcm_48k_mono = audioop.tomono(pcm_48k_stereo, 2, 0.5, 0.5)
        state = self._resample_state.get(user.id)
        pcm_16k_mono, new_state = audioop.ratecv(pcm_48k_mono, 2, 1, 48_000, 16_000, state)
        self._resample_state[user.id] = new_state

        buf = self._buffers.setdefault(user.id, UserAudioBuffer(user_id=user.id))
        buf.pcm16_mono_16khz.extend(pcm_16k_mono)
        buf.frame_count += 1

        if self.on_chunk and len(buf.pcm16_mono_16khz) >= self._target_chunk_bytes:
            payload = bytes(buf.pcm16_mono_16khz)
            buf.pcm16_mono_16khz.clear()
            self.on_chunk(user, payload)

    def flush_user(self, user_id: int) -> bytes:
        buf = self._buffers.get(user_id)
        if not buf:
            return b""
        payload = bytes(buf.pcm16_mono_16khz)
        buf.pcm16_mono_16khz.clear()
        return payload

    def cleanup(self):
        self._buffers.clear()
        self._resample_state.clear()
