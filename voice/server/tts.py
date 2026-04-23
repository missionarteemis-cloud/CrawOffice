"""TTS via ElevenLabs API — no local GPU required.

Uses eleven_flash_v2_5 for minimum latency (~400ms first byte).
Supports both full synthesis and streaming chunks.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, Iterator, Optional

logger = logging.getLogger(__name__)

# common short phrases that get cached in memory
_PHRASE_CACHE: dict[str, bytes] = {}
_CACHE_PHRASES = {
    "ok", "certo", "sì", "no", "capito", "un momento", "aspetta",
    "pronto", "eccomi", "dimmi", "vai pure", "fatto",
}


@dataclass
class TTSStats:
    total_requests: int = 0
    total_failures: int = 0
    total_latency_ms: float = 0.0
    cache_hits: int = 0

    @property
    def avg_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests


class ElevenLabsTTS:
    """ElevenLabs TTS client targeting <400ms first-byte latency.

    Model: eleven_flash_v2_5 (lowest latency ElevenLabs model)
    """

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_id: str = "eleven_flash_v2_5",
        output_format: str = "mp3_44100_128",
    ):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.output_format = output_format
        self._stats = TTSStats()
        self._client = None

    def load(self) -> None:
        """Initialize ElevenLabs client. Call once at startup."""
        from elevenlabs.client import ElevenLabs
        self._client = ElevenLabs(api_key=self.api_key)
        logger.info(f"ElevenLabsTTS ready: voice={self.voice_id} model={self.model_id}")

    @property
    def ready(self) -> bool:
        return self._client is not None

    @property
    def stats(self) -> TTSStats:
        return self._stats

    def synthesize(self, text: str) -> bytes:
        """Synthesize text to audio bytes (MP3).

        Uses in-memory cache for common short phrases.
        """
        text = text.strip()
        cache_key = text.lower()

        if cache_key in _PHRASE_CACHE:
            self._stats.cache_hits += 1
            logger.debug(f"TTS cache hit: '{text[:40]}'")
            return _PHRASE_CACHE[cache_key]

        if not self._client:
            raise RuntimeError("TTS not loaded — call load() first")

        t0 = time.time()
        try:
            audio = self._client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id=self.model_id,
                output_format=self.output_format,
            )
            # generator → bytes
            audio_bytes = b"".join(audio) if hasattr(audio, "__iter__") else audio
            latency_ms = (time.time() - t0) * 1000

            self._stats.total_requests += 1
            self._stats.total_latency_ms += latency_ms
            logger.debug(f"TTS: '{text[:40]}' latency={latency_ms:.0f}ms size={len(audio_bytes)}B")

            # cache common short phrases
            if cache_key in _CACHE_PHRASES or len(text) < 20:
                _PHRASE_CACHE[cache_key] = audio_bytes

            return audio_bytes

        except Exception as e:
            self._stats.total_failures += 1
            logger.error(f"TTS error: {e}")
            raise

    def synthesize_stream(self, text: str) -> Iterator[bytes]:
        """Stream audio chunks for lower perceived latency."""
        if not self._client:
            raise RuntimeError("TTS not loaded — call load() first")

        t0 = time.time()
        first_chunk = True
        try:
            stream = self._client.text_to_speech.convert_as_stream(
                voice_id=self.voice_id,
                text=text.strip(),
                model_id=self.model_id,
                output_format=self.output_format,
            )
            for chunk in stream:
                if chunk:
                    if first_chunk:
                        logger.debug(f"TTS first chunk in {(time.time()-t0)*1000:.0f}ms")
                        first_chunk = False
                    yield chunk
            self._stats.total_requests += 1
            self._stats.total_latency_ms += (time.time() - t0) * 1000
        except Exception as e:
            self._stats.total_failures += 1
            logger.error(f"TTS stream error: {e}")
            raise
