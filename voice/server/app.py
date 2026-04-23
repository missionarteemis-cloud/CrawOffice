"""FastAPI voice server — runs on PC fisso (RTX 4070).

Endpoints:
  GET  /health                         — status + GPU info
  POST /v1/audio/transcriptions        — STT (OpenAI-compatible)
  POST /v1/audio/speech                — TTS (OpenAI-compatible)
  GET  /v1/stats                       — latency statistics

Run:
  uvicorn voice.server.app:app --host 0.0.0.0 --port 8880
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import yaml
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from voice.server.stt import FasterWhisperSTT
from voice.server.tts import ElevenLabsTTS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(path: str = "voice/config.yaml") -> dict:
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning(f"Config not found at {path}, using defaults")
        return {}


cfg = load_config()
_stt_cfg = cfg.get("stt", {})
_tts_cfg = cfg.get("tts", {})

STT_MODEL = os.getenv("STT_MODEL", _stt_cfg.get("model", "small"))
STT_LANGUAGE = os.getenv("STT_LANGUAGE", _stt_cfg.get("language", "it")) or None
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", _tts_cfg.get("api_key", ""))
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", _tts_cfg.get("voice_id", ""))

# ---------------------------------------------------------------------------
# Engines (initialized at startup)
# ---------------------------------------------------------------------------

stt_engine: Optional[FasterWhisperSTT] = None
tts_engine: Optional[ElevenLabsTTS] = None
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global stt_engine, tts_engine

    logger.info("Starting voice server — loading STT...")
    stt_engine = FasterWhisperSTT(model_size=STT_MODEL, language=STT_LANGUAGE)
    stt_engine.load()

    if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
        logger.info("Loading TTS...")
        tts_engine = ElevenLabsTTS(api_key=ELEVENLABS_API_KEY, voice_id=ELEVENLABS_VOICE_ID)
        tts_engine.load()
    else:
        logger.warning("ELEVENLABS_API_KEY or ELEVENLABS_VOICE_ID not set — TTS disabled")

    logger.info("Voice server ready.")
    yield
    logger.info("Voice server shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Craw Voice Server", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    gpu_info = _get_gpu_info()
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - _start_time),
        "stt": {
            "ready": stt_engine is not None and stt_engine.ready,
            "model": STT_MODEL,
            "device": stt_engine.device if stt_engine else None,
        },
        "tts": {
            "ready": tts_engine is not None and tts_engine.ready,
            "provider": "elevenlabs",
        },
        "gpu": gpu_info,
    }


@app.post("/v1/audio/transcriptions")
async def transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = Form(default=None),
    model: Optional[str] = Form(default=None),  # ignored, for OpenAI compat
):
    """STT endpoint — OpenAI Whisper API compatible."""
    if not stt_engine or not stt_engine.ready:
        raise HTTPException(status_code=503, detail="STT engine not ready")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        result = stt_engine.transcribe(audio_bytes, language=language)
        return {
            "text": result.text,
            "language": result.language,
            "duration_seconds": result.duration_seconds,
            "latency_ms": result.latency_ms,
        }
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class TTSRequest(BaseModel):
    input: str
    voice: Optional[str] = None          # ignored if ELEVENLABS_VOICE_ID is set
    model: Optional[str] = None          # ignored, for OpenAI compat
    response_format: Optional[str] = "mp3"
    stream: bool = False


@app.post("/v1/audio/speech")
async def synthesize(req: TTSRequest):
    """TTS endpoint — OpenAI-compatible."""
    if not tts_engine or not tts_engine.ready:
        raise HTTPException(status_code=503, detail="TTS engine not ready")

    text = req.input.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty input text")

    try:
        if req.stream:
            def _gen():
                for chunk in tts_engine.synthesize_stream(text):
                    yield chunk
            return StreamingResponse(_gen(), media_type="audio/mpeg")
        else:
            audio_bytes = tts_engine.synthesize(text)
            return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/stats")
def stats():
    return {
        "stt": {
            "total_requests": stt_engine.stats.total_requests if stt_engine else 0,
            "total_failures": stt_engine.stats.total_failures if stt_engine else 0,
            "avg_latency_ms": round(stt_engine.stats.avg_latency_ms, 1) if stt_engine else 0,
        },
        "tts": {
            "total_requests": tts_engine.stats.total_requests if tts_engine else 0,
            "total_failures": tts_engine.stats.total_failures if tts_engine else 0,
            "avg_latency_ms": round(tts_engine.stats.avg_latency_ms, 1) if tts_engine else 0,
            "cache_hits": tts_engine.stats.cache_hits if tts_engine else 0,
        },
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_gpu_info() -> dict:
    try:
        import torch
        if torch.cuda.is_available():
            return {
                "available": True,
                "name": torch.cuda.get_device_name(0),
                "vram_total_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1),
                "vram_free_gb": round(
                    (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1e9, 1
                ),
            }
        return {"available": False}
    except Exception:
        return {"available": False}
