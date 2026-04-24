"""Discord slash commands — voice pipeline.

Pipeline per turn completo:
  audio in -> VAD chunk -> STT (PC) -> LLM (PC) -> TTS (PC) -> playback Discord

Busy flag: mentre il bot parla, i chunk audio vengono ignorati per evitare
che il microfono riprenda la voce del bot e scateni un loop.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time
from collections import deque
from typing import Optional

import discord
from discord import app_commands

from voice.bot.voice_session import VoiceSessionManager
from voice.pipeline.audio_sink import CrawAudioSink
from voice.pipeline.transcriber import PcTranscriber
from voice.pipeline.pc_llm_client import PcLLMClient
from voice.pipeline.pc_tts_client import PcTTSClient

logger = logging.getLogger(__name__)

# Quanti turn di storia tenere per contesto LLM (user + assistant alternati)
_HISTORY_TURNS = 6


class VoiceCommands(app_commands.Group):
    def __init__(self, *, session_manager: VoiceSessionManager):
        super().__init__(name="voice", description="Voice controls for Craw")
        self.session_manager = session_manager
        self.transcriber = PcTranscriber()
        self.llm = PcLLMClient()
        self.tts = PcTTSClient()
        self._tasks: dict[int, set[asyncio.Task]] = {}
        self._history: dict[int, deque] = {}

    def _track_task(self, guild_id: int, task: asyncio.Task) -> None:
        bucket = self._tasks.setdefault(guild_id, set())
        bucket.add(task)
        task.add_done_callback(lambda t: bucket.discard(t))

    def _is_busy(self, guild_id: int) -> bool:
        """True se il bot sta già parlando in quel guild."""
        session = self.session_manager.get(guild_id)
        if not session:
            return False
        vc = session.voice_client
        return bool(vc and vc.is_playing())

    async def _handle_turn(
        self,
        guild_id: int,
        text_channel: Optional[discord.abc.Messageable],
        user: discord.User,
        pcm16_mono_16khz: bytes,
    ) -> None:
        # Ignora se il bot sta già parlando (evita loop eco)
        if self._is_busy(guild_id):
            return

        session = self.session_manager.get(guild_id)
        if not session or not session.voice_client:
            return

        name = getattr(user, "display_name", str(user.id))

        # 1. STT
        t0 = time.monotonic()
        logger.info(f"→ STT: {len(pcm16_mono_16khz)} bytes per {name}")
        try:
            stt_result = await asyncio.to_thread(
                self.transcriber.transcribe_pcm16le,
                pcm16_mono_16khz,
                sample_rate_hz=16_000,
                channels=1,
                sample_width_bytes=2,
                filename=f"discord-user-{user.id}.wav",
            )
            text = (stt_result.text or "").strip()
            logger.info(f"← STT: '{text[:60]}' ({(time.monotonic()-t0)*1000:.0f}ms)")
        except Exception as e:
            logger.error(f"STT error ({(time.monotonic()-t0)*1000:.0f}ms): {e}")
            if text_channel:
                await text_channel.send(f"⚠️ errore STT: {e}")
            return

        if not text:
            return

        if text_channel:
            await text_channel.send(f"🎙️ {name}: {text}")

        # 2. LLM
        history = self._history.setdefault(guild_id, deque(maxlen=_HISTORY_TURNS * 2))
        history.append({"role": "user", "content": text})
        messages = list(history)

        t1 = time.monotonic()
        try:
            llm_result = await asyncio.to_thread(self.llm.chat, messages)
            reply_text = llm_result.text
            logger.info(f"← LLM: '{reply_text[:60]}' ({(time.monotonic()-t1)*1000:.0f}ms)")
        except Exception as e:
            logger.error(f"LLM error: {e}")
            if text_channel:
                await text_channel.send(f"⚠️ errore LLM: {e}")
            history.pop()
            return

        history.append({"role": "assistant", "content": reply_text})
        if text_channel:
            await text_channel.send(f"🤖 Craw: {reply_text}")

        # 3. TTS
        t2 = time.monotonic()
        try:
            tts_result = await asyncio.to_thread(self.tts.synthesize, reply_text)
            audio_bytes = tts_result.audio_bytes
            logger.info(f"← TTS: {len(audio_bytes)} bytes ({(time.monotonic()-t2)*1000:.0f}ms)")
        except Exception as e:
            logger.error(f"TTS error: {e}")
            if text_channel:
                await text_channel.send(f"⚠️ errore TTS: {e}")
            return

        # 4. Playback
        logger.info(f"pipeline totale: {(time.monotonic()-t0)*1000:.0f}ms")
        await self._play_audio(session.voice_client, audio_bytes)

    async def _play_audio(self, vc: discord.VoiceClient, mp3_bytes: bytes) -> None:
        if vc.is_playing():
            vc.stop()

        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        try:
            tmp.write(mp3_bytes)
            tmp.flush()
            tmp_path = tmp.name
        finally:
            tmp.close()

        def _after(error):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            if error:
                logger.error(f"Playback error: {error}")

        source = discord.FFmpegOpusAudio(tmp_path)
        vc.play(source, after=_after)

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

            session = await self.session_manager.join_member_channel(
                interaction.user,
                text_channel=interaction.channel,
            )

            guild_id = interaction.guild.id
            self._history[guild_id] = deque(maxlen=_HISTORY_TURNS * 2)

            sink = CrawAudioSink(
                on_chunk=lambda user, pcm: self._track_task(
                    guild_id,
                    asyncio.create_task(
                        self._handle_turn(guild_id, interaction.channel, user, pcm)
                    ),
                )
            )

            if not session.voice_client:
                await interaction.followup.send("Connessione vocale non disponibile.")
                return

            if hasattr(session.voice_client, "listen"):
                session.voice_client.listen(sink)
                self.session_manager.mark_listening(guild_id, True)
                self.session_manager.update_metadata(guild_id, sink=sink)
                await interaction.followup.send(
                    f"Entrato in **{interaction.user.voice.channel.name}** — ascolto e risposta attivi."
                )
            else:
                await interaction.followup.send(
                    "Entrato nel canale, ma questo voice client non espone ancora la ricezione audio (`listen`)."
                )
        except Exception as e:
            logger.error(f"Errore in /voice join: {type(e).__name__}: {e}")
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(f"⚠️ errore join: {type(e).__name__}: {e}")
                else:
                    await interaction.response.send_message(f"⚠️ errore join: {type(e).__name__}: {e}", ephemeral=True)
            except Exception:
                pass
            raise

    @app_commands.command(name="leave", description="Leave the active voice channel")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("Questo comando funziona solo in un server.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        guild_id = interaction.guild.id
        session = self.session_manager.get(guild_id)

        if session and session.voice_client and session.voice_client.is_playing():
            session.voice_client.stop()

        if session and session.metadata.get("sink"):
            session.metadata["sink"].cleanup()

        for task in list(self._tasks.get(guild_id, set())):
            task.cancel()

        self._history.pop(guild_id, None)

        left = await self.session_manager.leave_guild(guild_id)
        if left:
            await interaction.followup.send("Uscito dal canale vocale.")
        else:
            await interaction.followup.send("Non ero in nessun canale vocale attivo.")

    @app_commands.command(name="clear", description="Cancella la memoria della conversazione")
    async def clear(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("Questo comando funziona solo in un server.", ephemeral=True)
            return
        self._history.pop(interaction.guild.id, None)
        await interaction.response.send_message("Memoria conversazione cancellata.", ephemeral=True)
