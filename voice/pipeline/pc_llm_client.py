"""HTTP LLM client — calls /v1/chat/completions on the PC voice server."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx
import yaml


@dataclass
class LLMResult:
    text: str
    latency_ms: Optional[float] = None


class PcLLMClient:
    def __init__(self, config_path: str = "voice/config.yaml", timeout_seconds: float = 60.0):
        self.config_path = Path(config_path)
        self.timeout_seconds = timeout_seconds
        self.config = yaml.safe_load(self.config_path.read_text()) or {}
        pc = self.config.get("pc_server", {})
        host = pc.get("host", "127.0.0.1")
        port = pc.get("port", 8880)
        self.base_url = f"http://{host}:{port}"

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> LLMResult:
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = httpx.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return LLMResult(text=text, latency_ms=data.get("latency_ms"))
