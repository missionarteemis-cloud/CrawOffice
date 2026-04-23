import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Callable

import websockets
from websockets.asyncio.client import ClientConnection

logger = logging.getLogger(__name__)

GATEWAY_URL = "ws://127.0.0.1:18789"
GATEWAY_TOKEN = None  # loaded from config/env at runtime
GATEWAY_VERSION = "2026.4.15"


@dataclass
class CrawMessage:
    text: str
    session_key: str
    agent_id: str = "main"


@dataclass
class _PendingRequest:
    future: asyncio.Future
    chunks: list[str] = field(default_factory=list)
    streaming: bool = False


class CrawClient:
    """WebSocket client for openclaw-gateway.

    Handshake:
      1. Receive connect.challenge {nonce}
      2. Send req/connect with auth token + client info
      3. Receive res/connect ok → connection ready
    """

    def __init__(self, token: str, url: str = GATEWAY_URL):
        self.url = url
        self.token = token
        self._ws: ClientConnection | None = None
        self._pending: dict[str, _PendingRequest] = {}
        self._subscribers: dict[str, list[Callable]] = {}
        self._recv_task: asyncio.Task | None = None
        self._connected = asyncio.Event()

    # ------------------------------------------------------------------ connect

    async def connect(self) -> None:
        self._ws = await websockets.connect(self.url, open_timeout=5)
        self._recv_task = asyncio.create_task(self._recv_loop())
        await asyncio.wait_for(self._connected.wait(), timeout=10)
        logger.info("CrawClient connected to gateway")

    async def disconnect(self) -> None:
        if self._recv_task:
            self._recv_task.cancel()
        if self._ws:
            await self._ws.close()
        self._connected.clear()
        logger.info("CrawClient disconnected")

    # -------------------------------------------------------------- send/stream

    async def send(self, session_key: str, text: str, agent_id: str = "main") -> str:
        """Send a message and return the full response text."""
        req_id = str(uuid.uuid4())
        future: asyncio.Future[str] = asyncio.get_event_loop().create_future()
        self._pending[req_id] = _PendingRequest(future=future)
        await self._send_frame({
            "type": "req",
            "id": req_id,
            "method": "sessions.send",
            "params": {
                "key": session_key,
                "agentId": agent_id,
                "message": {"role": "user", "content": text},
            },
        })
        return await asyncio.wait_for(future, timeout=60)

    async def stream(
        self, session_key: str, text: str, agent_id: str = "main"
    ) -> AsyncIterator[str]:
        """Send a message and yield response text chunks as they arrive."""
        req_id = str(uuid.uuid4())
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def _on_chunk(chunk: str) -> None:
            await queue.put(chunk)

        async def _on_done() -> None:
            await queue.put(None)

        future: asyncio.Future[str] = asyncio.get_event_loop().create_future()
        pending = _PendingRequest(future=future, streaming=True)
        pending._queue = queue  # type: ignore[attr-defined]
        self._pending[req_id] = pending

        await self._send_frame({
            "type": "req",
            "id": req_id,
            "method": "sessions.send",
            "params": {
                "key": session_key,
                "agentId": agent_id,
                "message": {"role": "user", "content": text},
            },
        })

        while True:
            chunk = await asyncio.wait_for(queue.get(), timeout=60)
            if chunk is None:
                break
            yield chunk

    # ----------------------------------------------------------- session keys

    @staticmethod
    def voice_session_key(channel_id: str, agent_id: str = "main") -> str:
        """Session key for a Discord voice channel conversation."""
        return f"agent:{agent_id}:discord:voice:{channel_id}"

    @staticmethod
    def text_channel_key(channel_id: str, agent_id: str = "main") -> str:
        return f"agent:{agent_id}:discord:channel:{channel_id}"

    # ----------------------------------------------------------- internal

    async def _send_frame(self, frame: dict) -> None:
        if not self._ws:
            raise RuntimeError("not connected")
        await self._ws.send(json.dumps(frame))

    async def _recv_loop(self) -> None:
        try:
            async for raw in self._ws:  # type: ignore[union-attr]
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                await self._dispatch(msg)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("gateway connection closed")
            self._connected.clear()

    async def _dispatch(self, msg: dict) -> None:
        t = msg.get("type")

        if t == "event":
            event = msg.get("event")
            if event == "connect.challenge":
                nonce = msg["payload"]["nonce"]
                await self._send_connect(nonce)

            elif event == "session.message":
                await self._handle_session_message(msg)

        elif t == "res":
            req_id = msg.get("id")
            pending = self._pending.get(req_id)
            if not pending:
                return
            if not msg.get("ok"):
                err = msg.get("error", {})
                pending.future.set_exception(
                    RuntimeError(f"gateway error: {err.get(message, err)}")
                )
                self._pending.pop(req_id, None)
            else:
                payload = msg.get("payload", {})
                if payload.get("type") == "hello-ok":
                    self._connected.set()
                else:
                    # non-streaming response: resolve immediately
                    if not pending.streaming:
                        text = payload.get("text") or payload.get("content") or ""
                        pending.future.set_result(text)
                        self._pending.pop(req_id, None)

    async def _handle_session_message(self, msg: dict) -> None:
        payload = msg.get("payload", {})
        req_id = payload.get("requestId") or payload.get("reqId")
        pending = self._pending.get(req_id) if req_id else None

        role = payload.get("role")
        content = payload.get("content") or payload.get("text") or ""
        done = payload.get("done", False)

        if pending and pending.streaming:
            if content:
                await pending._queue.put(content)  # type: ignore[attr-defined]
            if done:
                await pending._queue.put(None)
                pending.future.set_result("".join(pending.chunks))
                self._pending.pop(req_id, None)
        elif pending and not pending.streaming and done:
            pending.future.set_result(content)
            self._pending.pop(req_id, None)

    async def _send_connect(self, nonce: str) -> None:
        await self._send_frame({
            "type": "req",
            "id": str(uuid.uuid4()),
            "method": "connect",
            "params": {
                "minProtocol": 3,
                "maxProtocol": 3,
                "client": {
                    "id": "gateway-client",
                    "version": GATEWAY_VERSION,
                    "platform": "darwin",
                    "mode": "backend",
                },
                "auth": {"token": self.token},
                "role": "operator",
                "caps": [],
                "scopes": [],
            },
        })
