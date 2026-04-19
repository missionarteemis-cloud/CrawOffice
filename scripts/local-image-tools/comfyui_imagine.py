#!/usr/bin/env python3
"""
comfyui_imagine.py — Genera immagini con ComfyUI in background e invia su Telegram quando pronta.

Questo script viene lanciato da OpenClaw e termina SUBITO dopo aver messo in coda la generazione.
ComfyUI genera in background, e quando finisce un processo separato invia la foto su Telegram.

Uso da OpenClaw / terminale:
  python3.11 comfyui_imagine.py "un tramonto su Napoli"
  python3.11 comfyui_imagine.py "un gatto astronauta" --no-telegram
  python3.11 comfyui_imagine.py "una pizza margherita" --width 768 --height 768
"""

import sys
import os
import json
import uuid
import time
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

COMFYUI_URL    = "http://127.0.0.1:8188"
OUTPUT_DIR     = Path.home() / "Desktop"
TELEGRAM_TOKEN = "8679210192:AAFe63h2XFvfqSnyu4gw0ZqIyTAkVrAFqZI"
TELEGRAM_CHAT  = "608537515"
CHECKPOINT     = "sdxl_base.safetensors"
SCRIPT_PATH    = Path(__file__).resolve()


def build_workflow(prompt, width=1024, height=1024, steps=25):
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": 7.0,
                "denoise": 1,
                "latent_image": ["5", 0],
                "model": ["4", 0],
                "negative": ["7", 0],
                "positive": ["6", 0],
                "sampler_name": "euler",
                "scheduler": "normal",
                "seed": int(uuid.uuid4().int % 2**32),
                "steps": steps
            }
        },
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CHECKPOINT}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"batch_size": 1, "height": height, "width": width}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": prompt}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": "blurry, low quality, ugly, deformed, watermark, text"}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "openclaw", "images": ["8", 0]}}
    }


def queue_prompt(workflow):
    payload = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["prompt_id"]


def get_image_path(prompt_id, timeout=3600):
    """Aspetta che ComfyUI finisca — questa funzione gira nel processo figlio in background."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10) as resp:
                history = json.loads(resp.read())
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        img = node_output["images"][0]
                        comfy_output = Path.home() / "ComfyUI" / "output"
                        subfolder = img.get("subfolder", "")
                        filename  = img["filename"]
                        return comfy_output / subfolder / filename if subfolder else comfy_output / filename
        except:
            pass
        time.sleep(5)
    return None


def copy_to_desktop(src_path, prompt):
    safe = "".join(c if c.isalnum() or c in " _-" else "" for c in prompt)[:40]
    safe = safe.strip().replace(" ", "_")
    ts   = time.strftime("%Y%m%d_%H%M%S")
    dest = OUTPUT_DIR / f"sd_{ts}_{safe}.png"
    dest.write_bytes(src_path.read_bytes())
    return dest


def send_telegram_message(text):
    """Invia un messaggio di testo su Telegram."""
    payload = json.dumps({"chat_id": TELEGRAM_CHAT, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def send_telegram_photo(img_path, caption):
    """Invia l'immagine su Telegram."""
    url      = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    boundary = "----Boundary7MA4"
    img_bytes = img_path.read_bytes()
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{TELEGRAM_CHAT}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n"
        .encode() + caption.encode() +
        f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{img_path.name}\"\r\nContent-Type: image/png\r\n\r\n"
        .encode() + img_bytes +
        f"\r\n--{boundary}--\r\n".encode()
    )
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def check_comfyui():
    try:
        urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=5)
        return True
    except:
        return False


def background_wait_and_send(prompt_id, prompt, send_telegram):
    """
    Questa funzione gira in un processo separato in background.
    Aspetta che ComfyUI finisca, poi manda la foto su Telegram.
    """
    img_path = get_image_path(prompt_id)
    if not img_path or not img_path.exists():
        if send_telegram:
            send_telegram_message(f"❌ Generazione fallita per: '{prompt}'")
        return

    desktop_path = copy_to_desktop(img_path, prompt)

    if send_telegram:
        try:
            send_telegram_photo(
                desktop_path,
                f"🎨 {prompt}\n🖥️ Generata in locale con Stable Diffusion SDXL"
            )
        except Exception as e:
            print(f"Errore Telegram: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt")
    parser.add_argument("--width",  type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps",  type=int, default=25)
    parser.add_argument("--no-telegram", action="store_true")
    parser.add_argument("--_background_prompt_id", help=argparse.SUPPRESS)
    args = parser.parse_args()

    # Modalità background — lanciata internamente, aspetta e manda Telegram
    if args._background_prompt_id:
        background_wait_and_send(
            args._background_prompt_id,
            args.prompt,
            not args.no_telegram
        )
        return

    # Modalità normale — verifica ComfyUI, mette in coda, torna subito
    if not check_comfyui():
        print("❌ ComfyUI non è in esecuzione!")
        print("   Avvialo con: cd ~/ComfyUI && python3.11 main.py --listen 127.0.0.1 --port 8188")
        if not args.no_telegram:
            send_telegram_message("❌ ComfyUI non è attivo sul Mac. Avvialo e riprova.")
        sys.exit(1)

    # Mette in coda la generazione
    workflow  = build_workflow(args.prompt, args.width, args.height, args.steps)
    prompt_id = queue_prompt(workflow)

    # Avvisa subito l'utente su Telegram
    if not args.no_telegram:
        send_telegram_message(
            f"⏳ Generazione avviata!\n"
            f"🎨 Prompt: '{args.prompt}'\n"
            f"🖥️ Stable Diffusion SDXL in locale\n"
            f"⏱️ Sul tuo M1 ci vuole circa 30 minuti — te la mando appena è pronta!"
        )

    print(f"✅ Generazione in coda! Job ID: {prompt_id}")
    print(f"   Te la mando su Telegram quando è pronta.")

    # Lancia il processo in background che aspetta e manda la foto
    subprocess.Popen([
        "python3.11", str(SCRIPT_PATH),
        args.prompt,
        "--_background_prompt_id", prompt_id,
        *(["--no-telegram"] if args.no_telegram else [])
    ])


if __name__ == "__main__":
    main()
