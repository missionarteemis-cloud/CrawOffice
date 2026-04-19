#!/usr/bin/env python3
"""
comfyui_img2img.py — Trasforma una immagine esistente con Stable Diffusion (Img2Img).

Uso:
  python3.11 comfyui_img2img.py "dipinto ad olio impressionista" --image ~/Desktop/foto.jpg
  python3.11 comfyui_img2img.py "render professionale su sfondo bianco" --image ~/foto.png --strength 0.6
  python3.11 comfyui_img2img.py "anime style" --image ~/foto.jpg --no-telegram

Parametri chiave:
  --strength: quanto l'AI modifica l'immagine (0.1=poco, 0.9=tanto). Default: 0.75
  --steps: passi di diffusione. Default: 20 (meno del txt2img perché parte già da un'immagine)
"""

import sys
import os
import json
import uuid
import time
import base64
import argparse
import urllib.request
import urllib.error
from pathlib import Path

COMFYUI_URL    = "http://127.0.0.1:8188"
OUTPUT_DIR     = Path.home() / "Desktop"
TELEGRAM_TOKEN = "8679210192:AAFe63h2XFvfqSnyu4gw0ZqIyTAkVrAFqZI"
TELEGRAM_CHAT  = "608537515"
CHECKPOINT     = "sdxl_base.safetensors"


def upload_image(image_path):
    """Carica l'immagine di input su ComfyUI."""
    img_bytes = Path(image_path).read_bytes()
    filename  = Path(image_path).name
    boundary  = "----Boundary7MA4"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{filename}\"\r\nContent-Type: image/png\r\n\r\n"
        .encode() + img_bytes +
        f"\r\n--{boundary}--\r\n".encode()
    )
    req = urllib.request.Request(
        f"{COMFYUI_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        return result["name"]


def build_img2img_workflow(prompt, image_name, strength=0.75, steps=20):
    """
    Workflow img2img:
    - Carica l'immagine originale
    - La codifica nello spazio latente (VAEEncode)
    - Applica il KSampler con denoise=strength (quanto modificare)
    - Decodifica e salva
    """
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": CHECKPOINT}
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name}
        },
        "3": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["2", 0],
                "vae": ["1", 2]
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": prompt
            }
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": "blurry, low quality, ugly, deformed, watermark, text, bad anatomy"
            }
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["3", 0],
                "seed": int(uuid.uuid4().int % 2**32),
                "steps": steps,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": strength  # chiave dell'img2img: quanto modificare l'originale
            }
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["6", 0],
                "vae": ["1", 2]
            }
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "openclaw_img2img",
                "images": ["7", 0]
            }
        }
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


def wait_for_completion(prompt_id, timeout=600):
    print("Trasformazione in corso", end="", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10) as resp:
            history = json.loads(resp.read())
        if prompt_id in history:
            print(" ✓")
            return history[prompt_id]
        print(".", end="", flush=True)
        time.sleep(2)
    print(" timeout!")
    return None


def get_image_path(history_entry):
    outputs = history_entry.get("outputs", {})
    for node_id, node_output in outputs.items():
        if "images" in node_output:
            img = node_output["images"][0]
            comfy_output = Path.home() / "ComfyUI" / "output"
            subfolder = img.get("subfolder", "")
            filename  = img["filename"]
            return comfy_output / subfolder / filename if subfolder else comfy_output / filename
    return None


def copy_to_desktop(src_path, prompt):
    safe = "".join(c if c.isalnum() or c in " _-" else "" for c in prompt)[:40]
    safe = safe.strip().replace(" ", "_")
    ts   = time.strftime("%Y%m%d_%H%M%S")
    dest = OUTPUT_DIR / f"img2img_{ts}_{safe}.png"
    dest.write_bytes(src_path.read_bytes())
    print(f"Salvata sul Desktop: {dest}")
    return dest


def send_telegram_photo(img_path, caption):
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
        result = json.loads(resp.read())
        if result.get("ok"):
            print("Inviata su Telegram!")
        else:
            print(f"Errore Telegram: {result}")


def check_comfyui():
    try:
        urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=5)
        return True
    except:
        return False


def main():
    parser = argparse.ArgumentParser(description="Img2Img con ComfyUI locale")
    parser.add_argument("prompt",   help="Stile o descrizione della trasformazione")
    parser.add_argument("--image",  required=True, help="Percorso immagine di input")
    parser.add_argument("--strength", type=float, default=0.75,
                        help="Intensità trasformazione 0.1-0.9 (default: 0.75)")
    parser.add_argument("--steps",  type=int, default=20)
    parser.add_argument("--no-telegram", action="store_true")
    args = parser.parse_args()

    if not check_comfyui():
        print("❌ ComfyUI non è in esecuzione!")
        print("   Avvialo con: cd ~/ComfyUI && python3.11 main.py --listen 127.0.0.1 --port 8188")
        sys.exit(1)

    image_path = Path(args.image).expanduser()
    if not image_path.exists():
        print(f"❌ Immagine non trovata: {image_path}")
        sys.exit(1)

    print(f"🖼️  Input: {image_path.name}")
    print(f"🎨 Prompt: '{args.prompt}'")
    print(f"   Strength: {args.strength} — Steps: {args.steps}")

    # Carica immagine su ComfyUI
    print("Caricamento immagine su ComfyUI...")
    image_name = upload_image(image_path)
    print(f"   Caricata come: {image_name}")

    # Genera
    workflow  = build_img2img_workflow(args.prompt, image_name, args.strength, args.steps)
    prompt_id = queue_prompt(workflow)
    print(f"   Job ID: {prompt_id}")

    history = wait_for_completion(prompt_id)
    if not history:
        print("❌ Timeout")
        sys.exit(1)

    img_path = get_image_path(history)
    if not img_path or not img_path.exists():
        print("❌ Immagine non trovata nell'output")
        sys.exit(1)

    desktop_path = copy_to_desktop(img_path, args.prompt)

    if not args.no_telegram:
        try:
            send_telegram_photo(
                desktop_path,
                f"🖼️ Img2Img completato!\n"
                f"🎨 Stile: {args.prompt}\n"
                f"💪 Strength: {args.strength}\n"
                f"🖥️ Generato in locale con Stable Diffusion"
            )
        except Exception as e:
            print(f"⚠️  Errore Telegram: {e} — immagine in: {desktop_path}")


if __name__ == "__main__":
    main()
