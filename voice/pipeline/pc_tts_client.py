"""HTTP TTS client — calls /v1/audio/speech on the PC voice server."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx
import yaml


@dataclass
class TTSResult:
    audio_bytes: bytes
    latency_ms: float


class PcTTSClient:
    def __init__(self, config_path: str = "voice/config.yaml", timeout_seconds: float = 30.0):
        self.config_path = Path(config_path)
        self.timeout_seconds = timeout_seconds
        self.config = yaml.safe_load(self.config_path.read_text()) or {}
        pc = self.config.get("pc_server", {})
        host = pc.get("host", "127.0.0.1")
        port = pc.get("port", 8880)
        self.base_url = f"http://{host}:{port}"

    def synthesize(self, text: str) -> TTSResult:
        import time
        t0 = time.monotonic()
        resp = httpx.post(
            f"{self.base_url}/v1/audio/speech",
            json={"input": text, "response_format": "mp3"},
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        latency_ms = (time.monotonic() - t0) * 1000
        return TTSResult(audio_bytes=resp.content, latency_ms=round(latency_ms, 1))
