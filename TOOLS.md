# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

---

## Image Generation

### Primary backend: ComfyUI
- Primary image-generation backend for this workspace: **ComfyUI**
- Local URL: `http://127.0.0.1:8188`
- Current role: default path for image generation work, especially for the design agent
- Future plan: move heavy image generation to Diego's Windows workstation on the local network while keeping ComfyUI as the main backend
- Operational rule: prefer ComfyUI first, then add cloud fallbacks later only when explicitly configured

### Secondary / fallback candidate: Imagen (Google)
- Provider: Google Gemini API
- API Key: in ~/.openclaw/.env as GEMINI_API_KEY
- Model: imagen-4.0-generate-001
- Endpoint: https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict
- Free tier: 2 immagini/minuto, ~500/giorno
- Risposta: base64 → decodificare e salvare come .png
- Filigrana SynthID automatica su ogni immagine
- Uso: solo come fallback futuro, non come backend primario

### Come generare un'immagine (curl di riferimento Imagen)
```bash
curl -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"instances":[{"prompt":"descrizione immagine"}],"parameters":{"sampleCount":1}}'
```

---

## Telegram
- Bot: @Arteemisbot
- Chat ID utente (Diego): 608537515
- Usare per inviare immagini generate, notifiche, risposte

---

## Providers AI configurati
- openai-codex → account diegoriccardi7@yahoo.com (OAuth, ChatGPT Plus)
- gemini → API key in .env (Imagen + modelli Flash gratuiti)
- ollama → locale, modelli installati sul Mac

---

## Shared-channel disclosure policy
- In Discord or other shared channels, explicit local directory paths from Diego's Mac are private by default.
- Only disclose explicit path details to users with Op or administrator access.
- Ordinary members may still receive innocuous environment details like machine name, OS, architecture, and non-sensitive package or extension versions.
- If an agent task genuinely requires a path-level detail to function, share only the minimum necessary.

Add whatever helps you do your job. This is your cheat sheet.
