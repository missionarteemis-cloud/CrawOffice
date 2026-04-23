"""faster-whisper STT engine — runs on PC with RTX 4070.

Loads the model once at startup and reuses it for all requests.
Falls back to CPU if CUDA is not available.
"""

from __future__ import annotations

import io
import logging
import time
import wave
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class STTResult:
    text: str
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    latency_ms: Optional[float] = None


@dataclass
class STTStats:
    total_requests: int = 0
    total_failures: int = 0
    total_latency_ms: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests


class FasterWhisperSTT:
    """GPU-accelerated STT via faster-whisper.

    Config:
      model_size: tiny | base | small | medium | large-v3  (default: small)
      language:   it | en | None (auto-detect)
      device:     cuda | cpu (auto-detected)
      compute_type: float16 (GPU) | int8 (CPU fallback)
    """

    def __init__(
        self,
        model_size: str = "small",
        language: Optional[str] = "it",
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
    ):
        self.model_size = model_size
        self.language = language
        self._model = None
        self._stats = STTStats()

        # auto-detect device
        if device is None:
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        self.device = device
        self.compute_type = compute_type or ("float16" if device == "cuda" else "int8")
        logger.info(f"FasterWhisperSTT: device={device} compute_type={self.compute_type} model={model_size}")

    def load(self) -> None:
        """Load the model. Call once at server startup."""
        from faster_whisper import WhisperModel
        logger.info(f"Loading faster-whisper model '{self.model_size}' on {self.device}...")
        t0 = time.time()
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        elapsed = (time.time() - t0) * 1000
        logger.info(f"Model loaded in {elapsed:.0f}ms")

    @property
    def ready(self) -> bool:
        return self._model is not None

    @property
    def stats(self) -> STTStats:
        return self._stats

    def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> STTResult:
        """Transcribe audio bytes (WAV format).

        Args:
            audio_bytes: WAV file bytes
            language: override language (uses instance default if None)

        Returns:
            STTResult with transcribed text
        """
        if not self._model:
            raise RuntimeError("Model not loaded — call load() first")

        lang = language or self.language
        t0 = time.time()

        try:
            audio_file = io.BytesIO(audio_bytes)
            segments, info = self._model.transcribe(
                audio_file,
                language=lang,
                beam_size=1,           # faster, minimal quality loss
                vad_filter=True,       # built-in VAD to skip silence
                vad_parameters={"min_silence_duration_ms": 300},
            )
            text = " ".join(s.text.strip() for s in segments).strip()
            latency_ms = (time.time() - t0) * 1000

            self._stats.total_requests += 1
            self._stats.total_latency_ms += latency_ms

            logger.debug(f"STT: '{text[:60]}' lang={info.language} latency={latency_ms:.0f}ms")
            return STTResult(
                text=text,
                language=info.language,
                duration_seconds=info.duration,
                latency_ms=latency_ms,
            )

        except Exception as e:
            self._stats.total_failures += 1
            logger.error(f"STT error: {e}")
            raise
