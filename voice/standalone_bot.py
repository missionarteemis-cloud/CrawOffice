"""Standalone Discord voice runner for the first real voice MVP.

This runner uses the existing Discord bot token but runs outside the OpenClaw
Discord runtime, so we can test:
- slash command registration
- /voice join and /voice leave
- audio receive
- STT handoff to the PC server

Run example:
  python3 -m voice.standalone_bot
"""

from __future__ import annotations

import os
from pathlib import Path

import discord
from discord.ext import commands
from discord.ext.voice_recv import VoiceRecvClient
from dotenv import load_dotenv

from voice.bot.voice_commands import VoiceCommands
from voice.bot.voice_session import VoiceSessionManager


def load_opus() -> None:
    opus_path = "/opt/homebrew/lib/libopus.dylib"
    if not discord.opus.is_loaded():
        discord.opus.load_opus(opus_path)


def load_discord_token() -> str:
    load_dotenv(Path.home() / ".openclaw" / ".env")
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN not found in ~/.openclaw/.env")
    return token


def load_guild_id() -> int | None:
    raw = os.getenv("DISCORD_GUILD_ID")
    if not raw:
        # fallback: legge da voice/config.yaml
        try:
            import yaml
            cfg = yaml.safe_load(open("voice/config.yaml")) or {}
            raw = str(cfg.get("discord", {}).get("guild_id", ""))
        except Exception:
            pass
    return int(raw) if raw and raw.isdigit() else None


class StandaloneVoiceBot(commands.Bot):
    def __init__(self, guild_id: int | None = None):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents, voice_client_class=VoiceRecvClient)
        self.voice_session_manager = VoiceSessionManager()
        self._guild_id = guild_id

    async def setup_hook(self):
        self.tree.add_command(VoiceCommands(session_manager=self.voice_session_manager))
        if self._guild_id:
            # guild sync — immediato (< 1 secondo)
            guild = discord.Object(id=self._guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Slash commands synced to guild {self._guild_id} (instant)")
        else:
            # global sync — può richiedere fino a 1 ora su Discord
            await self.tree.sync()
            print("Slash commands synced globally (may take up to 1h to appear)")

    async def on_ready(self):
        print(f"Voice bot ready as {self.user} ({self.user.id})")


def main():
    load_opus()
    guild_id = load_guild_id()
    bot = StandaloneVoiceBot(guild_id=guild_id)
    token = load_discord_token()
    bot.run(token)


if __name__ == "__main__":
    main()
