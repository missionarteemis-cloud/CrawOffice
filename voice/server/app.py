# FastAPI server — runs on PC fisso
# Exposes OpenAI-compatible endpoints:
#   POST /v1/audio/transcriptions  -> faster-whisper STT
#   POST /v1/audio/speech          -> ElevenLabs TTS
#   GET  /health
# TODO: adapt from openclaw-voice/server/app.py
