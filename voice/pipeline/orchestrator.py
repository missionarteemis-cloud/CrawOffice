# Main pipeline coordinator: audio_in -> vad -> turn_detect -> stt -> craw -> tts -> audio_out
# Handles barge-in, per-user state machines, streaming TTS playback
# TODO: adapt from openclaw-voice/pipeline/orchestrator.py — remove relevance filter, connect to Craw
