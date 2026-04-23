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
- openrouter → API key in .env, fallback automatico quando OpenAI non risponde

---

## Discord Admin (workaround per azioni non supportate dal tool nativo)

### Quando usarlo
Il tool Discord nativo di OpenClaw NON supporta nativamente:
- Creare canali (`channelCreate`)
- Eliminare canali (`channelDelete`)
- Creare categorie
- Creare thread standalone
- Creare thread da un messaggio esistente
- Inviare messaggi in thread specifici

Per queste azioni, usa lo script Python:
`~/.openclaw/workspace/scripts/discord_admin.py`

### Guild ID
`1495429636111204403`

### Regola operativa sui thread
Comportamento atteso:
- Primo messaggio su un topic → risposta nel canale principale
- Secondo messaggio sullo stesso topic → crea thread con nome sintetico, sposta la conversazione lì
- Nel thread: aggiungi recap/contesto minimo come primo messaggio

### Comandi disponibili

```bash
# ── CANALI ──────────────────────────────────────────────────────────────

# Crea un canale testuale
python3 ~/.openclaw/workspace/scripts/discord_admin.py create-channel --name "nome-canale" --type text

# Crea un canale vocale
python3 ~/.openclaw/workspace/scripts/discord_admin.py create-channel --name "vocale-team" --type voice

# Crea un canale dentro una categoria
python3 ~/.openclaw/workspace/scripts/discord_admin.py create-channel --name "chat" --type text --category CATEGORY_ID

# Crea una categoria
python3 ~/.openclaw/workspace/scripts/discord_admin.py create-category --name "TEAM ALPHA"

# Lista tutti i canali con ID
python3 ~/.openclaw/workspace/scripts/discord_admin.py list-channels

# Elimina un canale
python3 ~/.openclaw/workspace/scripts/discord_admin.py delete-channel --id CHANNEL_ID

# Imposta permessi
python3 ~/.openclaw/workspace/scripts/discord_admin.py set-permissions --channel-id ID --role-id ID --allow "VIEW_CHANNEL,SEND_MESSAGES"

# Modifica un canale
python3 ~/.openclaw/workspace/scripts/discord_admin.py edit-channel --id CHANNEL_ID --name "nuovo-nome"

# ── THREAD ──────────────────────────────────────────────────────────────

# Crea un thread standalone (con primo messaggio opzionale)
python3 ~/.openclaw/workspace/scripts/discord_admin.py create-thread \
  --channel-id CHANNEL_ID \
  --name "Nome thread" \
  --message "Recap: stiamo parlando di X..."

# Crea un thread da un messaggio esistente
python3 ~/.openclaw/workspace/scripts/discord_admin.py thread-from-message \
  --channel-id CHANNEL_ID \
  --message-id MESSAGE_ID \
  --name "Nome thread"

# Invia un messaggio in un thread esistente
python3 ~/.openclaw/workspace/scripts/discord_admin.py send-to-thread \
  --thread-id THREAD_ID \
  --message "Continuiamo qui la discussione su X"

# Lista thread attivi in un canale
python3 ~/.openclaw/workspace/scripts/discord_admin.py list-threads --channel-id CHANNEL_ID
```

### Parametro --auto-archive
Disponibile su create-thread e thread-from-message:
- 60 = archivia dopo 1 ora di inattività
- 1440 = archivia dopo 1 giorno (default)
- 4320 = archivia dopo 3 giorni
- 10080 = archivia dopo 7 giorni

---

## Shared-channel disclosure policy
- In Discord or other shared channels, explicit local directory paths from Diego's Mac are private by default.
- Only disclose explicit path details to users with Op or administrator access.
- Ordinary members may still receive innocuous environment details like machine name, OS, architecture, and non-sensitive package or extension versions.
- If an agent task genuinely requires a path-level detail to function, share only the minimum necessary.

## Discord server channel-access notes

### Default onboarding question
- Ask server admins: **In quali canali posso leggerti e risponderti?**
- Default if unspecified: I may read and reply in all channels.
- Explicit exclusions override general allow rules.
- Excluded channels should be treated as no-access when possible: no reading, no replying.

### Current server: 1495429636111204403
- Default server policy: reading and replying allowed in all channels unless an admin says otherwise.
- Current exception: do not read or reply in `#generale` (channel ID `1495445733564879068`).
- Intent for `#generale`: human-only conversation, invisible to the bot when possible.

Add whatever helps you do your job. This is your cheat sheet.
