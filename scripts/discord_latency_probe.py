#!/usr/bin/env python3
"""
Simple Discord latency probe for OpenClaw.

Reads recent messages from a target channel using the bot token, then estimates
response latency by pairing a user's message with the next bot reply that
references it via message_reference.

Usage:
  python3 scripts/discord_latency_probe.py --channel-id 1495429637944119348 --limit 100
  python3 scripts/discord_latency_probe.py --channel-id 1495429637944119348 --user-id 457986055489060877 --bot-id 1495436584990802051
"""

import argparse
import json
import os
import statistics
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENV_PATH = Path.home() / ".openclaw" / ".env"
API_BASE = "https://discord.com/api/v10"


def load_env(path: Path):
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def get_bot_token():
    env = load_env(ENV_PATH)
    token = env.get("DISCORD_BOT_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("DISCORD_BOT_TOKEN not found in ~/.openclaw/.env")
    return token


def api_get(endpoint: str):
    token = get_bot_token()
    req = urllib.request.Request(
        f"{API_BASE}{endpoint}",
        headers={
            "Authorization": f"Bot {token}",
            "User-Agent": "OpenClaw-DiscordLatencyProbe/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def fmt_ms(ms: float) -> str:
    if ms >= 1000:
        return f"{ms/1000:.1f}s"
    return f"{ms:.1f}ms"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel-id", required=True)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--user-id")
    ap.add_argument("--bot-id", default="1495436584990802051")
    args = ap.parse_args()

    messages = api_get(f"/channels/{args.channel_id}/messages?limit={args.limit}")
    messages = list(reversed(messages))

    by_id = {m["id"]: m for m in messages}
    pairs = []

    for msg in messages:
        if msg.get("author", {}).get("id") != args.bot_id:
            continue
        ref = (msg.get("message_reference") or {}).get("message_id")
        if not ref or ref not in by_id:
            continue
        user_msg = by_id[ref]
        if args.user_id and user_msg.get("author", {}).get("id") != args.user_id:
            continue
        if user_msg.get("author", {}).get("bot"):
            continue
        delta_ms = (parse_ts(msg["timestamp"]) - parse_ts(user_msg["timestamp"])).total_seconds() * 1000
        pairs.append({
            "user_message_id": user_msg["id"],
            "bot_message_id": msg["id"],
            "user_text": (user_msg.get("content") or "").strip(),
            "bot_text": (msg.get("content") or "").strip(),
            "latency_ms": delta_ms,
            "user_timestamp": user_msg["timestamp"],
            "bot_timestamp": msg["timestamp"],
        })

    if not pairs:
        print("No reply-linked message pairs found.")
        sys.exit(1)

    vals = [p["latency_ms"] for p in pairs]
    print(f"Found {len(pairs)} reply-linked pairs in channel {args.channel_id}\n")
    print(f"avg: {fmt_ms(statistics.mean(vals))}")
    print(f"min: {fmt_ms(min(vals))}")
    print(f"max: {fmt_ms(max(vals))}")
    if len(vals) >= 2:
        print(f"median: {fmt_ms(statistics.median(vals))}")

    print("\nRecent pairs:")
    for p in pairs[-10:]:
        preview = p['user_text'][:60].replace("\n", " ") or "[empty]"
        print(f"- {preview} -> {fmt_ms(p['latency_ms'])}")


if __name__ == "__main__":
    main()
