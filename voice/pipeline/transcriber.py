"""HTTP STT client for the PC voice server.

This is the first real bridge between Discord-side audio handling on the Mac and
GPU-backed STT on the Windows PC.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json
import wave
import io

import httpx
import yaml


@dataclass
class TranscriptionResult:
    text: str
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    raw: Optional[dict] = None


class PcTranscriber:
    def __init__(self, config_path: str = "voice/config.yaml", timeout_seconds: float = 60.0):
        self.config_path = Path(config_path)
        self.timeout_seconds = timeout_seconds
        self.config = self._load_config()
        self.base_url = self._resolve_base_url()
        self.language = self.config.get("stt", {}).get("language")

    def _load_config(self) -> dict:
        return yaml.safe_load(self.config_path.read_text()) or {}

    def _resolve_base_url(self) -> str:
        pc = self.config.get("pc_server", {})
        host = pc.get("host", "127.0.0.1")
        port = pc.get("port", 8880)
        return f"http://{host}:{port}"

    def transcribe_wav_bytes(self, wav_bytes: bytes, filename: str = "audio.wav") -> TranscriptionResult:
        files = {
            "file": (filename, wav_bytes, "audio/wav"),
        }
        data = {}
        if self.language:
            data["language"] = self.language

        response = httpx.post(
            f"{self.base_url}/v1/audio/transcriptions",
            files=files,
            data=data,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return TranscriptionResult(
            text=payload.get("text", ""),
            language=payload.get("language"),
            duration_seconds=payload.get("duration_seconds"),
            raw=payload,
        )

    def transcribe_pcm16le(
        self,
        pcm_bytes: bytes,
        *,
        sample_rate_hz: int = 48_000,
        channels: int = 1,
        sample_width_bytes: int = 2,
        filename: str = "audio.wav",
    ) -> TranscriptionResult:
        wav_bytes = self._pcm_to_wav_bytes(
            pcm_bytes,
            sample_rate_hz=sample_rate_hz,
            channels=channels,
            sample_width_bytes=sample_width_bytes,
        )
        return self.transcribe_wav_bytes(wav_bytes, filename=filename)

    def _pcm_to_wav_bytes(
        self,
        pcm_bytes: bytes,
        *,
        sample_rate_hz: int,
        channels: int,
        sample_width_bytes: int,
    ) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width_bytes)
            wf.setframerate(sample_rate_hz)
            wf.writeframes(pcm_bytes)
        return buf.getvalue()
