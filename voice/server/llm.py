"""LLM engine — wraps Ollama running locally on the PC (CUDA).

Exposes a single synchronous call:
    result = OllamaLLM(model="llama3.1:8b").chat(messages)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class LLMStats:
    total_requests: int = 0
    total_failures: int = 0
    _latencies: list = field(default_factory=list)

    @property
    def avg_latency_ms(self) -> float:
        return sum(self._latencies) / len(self._latencies) if self._latencies else 0.0

    def record(self, latency_ms: float) -> None:
        self.total_requests += 1
        self._latencies.append(latency_ms)
        if len(self._latencies) > 100:
            self._latencies.pop(0)


@dataclass
class ChatResult:
    text: str
    model: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0


SYSTEM_PROMPT = (
    "Sei Craw, un assistente vocale su Discord. "
    "Rispondi sempre in italiano. "
    "Tieni le risposte brevi e dirette, massimo 2-3 frasi. "
    "Non usare elenchi puntati né markdown — parla in modo naturale come faresti in una conversazione."
)


class OllamaLLM:
    def __init__(
        self,
        model: str = "llama3.1:8b",
        ollama_url: str = "http://localhost:11434",
        timeout_seconds: float = 60.0,
        system_prompt: str = SYSTEM_PROMPT,
    ):
        self.model = model
        self.ollama_url = ollama_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.system_prompt = system_prompt
        self.stats = LLMStats()
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    def load(self) -> None:
        """Verify Ollama is reachable and the model is available."""
        try:
            resp = httpx.get(f"{self.ollama_url}/api/tags", timeout=5.0)
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            # accept both "llama3.1:8b" and "llama3.1:8b-instruct-q4_K_M" etc.
            base = self.model.split(":")[0]
            if not any(base in m for m in models):
                logger.warning(
                    f"Model '{self.model}' not found in Ollama. Available: {models}. "
                    "Run: ollama pull llama3.1:8b"
                )
            self._ready = True
            logger.info(f"OllamaLLM ready — model={self.model} url={self.ollama_url}")
        except Exception as e:
            logger.error(f"OllamaLLM failed to connect to Ollama: {e}")
            self._ready = False

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int = 300,
    ) -> ChatResult:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_prompt}] + messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        t0 = time.monotonic()
        try:
            resp = httpx.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=self.timeout_seconds,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            self.stats.total_failures += 1
            raise RuntimeError(f"Ollama request failed: {e}") from e

        latency_ms = (time.monotonic() - t0) * 1000
        self.stats.record(latency_ms)

        msg = data.get("message", {})
        text = msg.get("content", "").strip()
        usage = data.get("usage", {})

        return ChatResult(
            text=text,
            model=self.model,
            latency_ms=round(latency_ms, 1),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
