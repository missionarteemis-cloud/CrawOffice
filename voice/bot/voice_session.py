"""Voice session management for Discord guilds.

First milestone responsibilities:
- track one active voice connection per guild
- join and leave voice channels cleanly
- keep enough session state to attach audio receive/transcription next
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import discord


@dataclass
class GuildVoiceSession:
    guild_id: int
    channel_id: int
    text_channel_id: Optional[int] = None
    voice_client: Optional[discord.VoiceClient] = None
    is_listening: bool = False
    metadata: dict = field(default_factory=dict)

    @property
    def connected(self) -> bool:
        return bool(self.voice_client and self.voice_client.is_connected())


class VoiceSessionManager:
    """Tracks active Discord voice sessions keyed by guild id."""

    def __init__(self):
        self._sessions: Dict[int, GuildVoiceSession] = {}

    def get(self, guild_id: int) -> Optional[GuildVoiceSession]:
        return self._sessions.get(guild_id)

    def all_sessions(self) -> Dict[int, GuildVoiceSession]:
        return dict(self._sessions)

    async def join_member_channel(
        self,
        member: discord.Member,
        *,
        text_channel: Optional[discord.abc.Messageable] = None,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> GuildVoiceSession:
        if not member.guild:
            raise ValueError("Member is not associated with a guild")
        if not member.voice or not member.voice.channel:
            raise ValueError("Member is not connected to a voice channel")

        guild = member.guild
        target_channel = member.voice.channel
        existing = guild.voice_client

        if existing and existing.is_connected():
            if existing.channel and existing.channel.id != target_channel.id:
                await existing.move_to(target_channel)
            voice_client = existing
        else:
            voice_client = await target_channel.connect(self_deaf=self_deaf, self_mute=self_mute)

        session = GuildVoiceSession(
            guild_id=guild.id,
            channel_id=target_channel.id,
            text_channel_id=getattr(text_channel, "id", None),
            voice_client=voice_client,
            is_listening=False,
        )
        self._sessions[guild.id] = session
        return session

    async def leave_guild(self, guild_id: int) -> bool:
        session = self._sessions.get(guild_id)
        if not session:
            return False

        vc = session.voice_client
        if vc and vc.is_connected():
            await vc.disconnect(force=False)

        self._sessions.pop(guild_id, None)
        return True

    async def cleanup_guild_client(self, guild: discord.Guild) -> None:
        session = self._sessions.get(guild.id)
        if not session:
            return
        vc = guild.voice_client
        if vc is None or not vc.is_connected():
            self._sessions.pop(guild.id, None)

    def mark_listening(self, guild_id: int, listening: bool = True) -> None:
        session = self._sessions.get(guild_id)
        if session:
            session.is_listening = listening

    def update_metadata(self, guild_id: int, **metadata) -> None:
        session = self._sessions.get(guild_id)
        if session:
            session.metadata.update(metadata)
