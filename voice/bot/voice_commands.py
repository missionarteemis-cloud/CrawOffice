"""Discord slash commands for the first voice milestone.

Goal of this command layer:
- /join -> join caller voice channel, attach sink, start transcription handoff
- /leave -> disconnect and clear guild voice session
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

import discord
from discord import app_commands

logger = logging.getLogger(__name__)

from voice.bot.voice_session import VoiceSessionManager
from voice.pipeline.audio_sink import CrawAudioSink
from voice.pipeline.transcriber import PcTranscriber


class VoiceCommands(app_commands.Group):
    def __init__(self, *, session_manager: VoiceSessionManager):
        super().__init__(name="vtest", description="Voice test controls for Craw")
        self.session_manager = session_manager
        self.transcriber = PcTranscriber()
        self._tasks: dict[int, set[asyncio.Task]] = {}

    def _track_task(self, guild_id: int, task: asyncio.Task) -> None:
        bucket = self._tasks.setdefault(guild_id, set())
        bucket.add(task)
        task.add_done_callback(lambda t: bucket.discard(t))

    async def _transcribe_chunk(
        self,
        guild_id: int,
        text_channel: Optional[discord.abc.Messageable],
        user: discord.User,
        pcm16_mono_16khz: bytes,
    ) -> None:
        t0 = time.time()
        name = getattr(user, 'display_name', str(user.id))
        logger.info(f"→ STT: inviando {len(pcm16_mono_16khz)} bytes per {name}")
        try:
            result = await asyncio.to_thread(
                self.transcriber.transcribe_pcm16le,
                pcm16_mono_16khz,
                sample_rate_hz=16_000,
                channels=1,
                sample_width_bytes=2,
                filename=f"discord-user-{user.id}.wav",
            )
            elapsed = (time.time() - t0) * 1000
            text = (result.text or "").strip()
            logger.info(f"← STT: '{text[:60]}' ({elapsed:.0f}ms)")
            if text and text_channel is not None:
                await text_channel.send(f"🎙️ {name}: {text}")
            elif not text:
                logger.info(f"STT: risposta vuota (silenzio o parlato non riconosciuto)")
        except Exception as e:
            elapsed = (time.time() - t0) * 1000
            logger.error(f"STT error dopo {elapsed:.0f}ms: {type(e).__name__}: {e}")
            if text_channel is not None:
                await text_channel.send(f"⚠️ errore trascrizione voice: {type(e).__name__}: {e}")

    @app_commands.command(name="join", description="Join your current voice channel")
    async def join(self, interaction: discord.Interaction):
        try:
            if interaction.guild is None or not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message("Questo comando funziona solo in un server.", ephemeral=True)
                return

            if interaction.user.voice is None or interaction.user.voice.channel is None:
                await interaction.response.send_message("Devi prima entrare in un canale vocale.", ephemeral=True)
                return

            await interaction.response.defer(thinking=True)
            await interaction.followup.send("step 1/5: defer ok, provo il join del canale vocale")

            session = await self.session_manager.join_member_channel(
                interaction.user,
                text_channel=interaction.channel,
            )
            await interaction.followup.send("step 2/5: join_member_channel completato")

            sink = CrawAudioSink(
                on_chunk=lambda user, pcm: self._track_task(
                    interaction.guild.id,
                    asyncio.create_task(
                        self._transcribe_chunk(interaction.guild.id, interaction.channel, user, pcm)
                    ),
                )
            )
            await interaction.followup.send("step 3/5: sink creato")

            if not session.voice_client:
                await interaction.followup.send("Connessione vocale non disponibile.")
                return

            vc = session.voice_client
            await interaction.followup.send(
                f"step 4/5: vc type={type(vc)}, has listen={hasattr(vc, 'listen')}"
            )

            if hasattr(session.voice_client, "listen"):
                session.voice_client.listen(sink)
                self.session_manager.mark_listening(interaction.guild.id, True)
                self.session_manager.update_metadata(interaction.guild.id, sink=sink)
                await interaction.followup.send(
                    f"step 5/5: Entrato in **{interaction.user.voice.channel.name}** e ascolto attivo."
                )
            else:
                await interaction.followup.send(
                    "step 5/5: Entrato nel canale, ma questo voice client non espone ancora la ricezione audio (`listen`)."
                )
        except Exception as e:
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(f"errore in /vtest join: {type(e).__name__}: {e}")
                else:
                    await interaction.response.send_message(f"errore in /vtest join: {type(e).__name__}: {e}", ephemeral=True)
            except Exception:
                pass
            raise

    @app_commands.command(name="leave", description="Leave the active voice channel")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("Questo comando funziona solo in un server.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)
        session = self.session_manager.get(interaction.guild.id)
        if session and session.metadata.get("sink"):
            session.metadata["sink"].cleanup()

        task_bucket = self._tasks.get(interaction.guild.id, set())
        for task in list(task_bucket):
            task.cancel()

        left = await self.session_manager.leave_guild(interaction.guild.id)
        if left:
            await interaction.followup.send("Uscito dal canale vocale.")
        else:
            await interaction.followup.send("Non ero in nessun canale vocale attivo.")
