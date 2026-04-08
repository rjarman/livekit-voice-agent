"""
Qwen-Omni-Realtime plugin for LiveKit Agents — DEBUG VERSION.

Handles DashScope protocol differences from OpenAI with extensive logging.
"""

import asyncio
import json
import logging
import os
from typing import Any, Optional

import aiohttp
from livekit.agents import APIConnectOptions
from livekit.agents._exceptions import APIConnectionError
from livekit.plugins.openai.realtime import (
    RealtimeModel as OpenAIRealtimeModel,
    RealtimeSession as OpenAIRealtimeSession,
)
from livekit.plugins.openai.realtime.realtime_model import process_base_url

logger = logging.getLogger("livekit.plugins.qwen")

DASHSCOPE_INTL_BASE_URL = "https://dashscope-intl.aliyuncs.com/api-ws/v1/realtime"
DASHSCOPE_CN_BASE_URL = "https://dashscope.aliyuncs.com/api-ws/v1/realtime"

DEFAULT_MODEL = "qwen-omni-turbo-realtime"
DEFAULT_VOICE = "Cherry"


class QwenRealtimeSession(OpenAIRealtimeSession):
    """Session with DashScope-specific fixes and debug logging."""

    def __init__(self, realtime_model: "RealtimeModel") -> None:
        super().__init__(realtime_model)
        self._last_response_create_event_id: str | None = None
        self._audio_chunks_received = 0
        self._generation_created_emitted = False
        self.on("openai_client_event_queued", self._fix_outgoing)
        self.on("openai_server_event_received", self._fix_incoming)
        # Also monitor generation events
        self.on("generation_created", self._on_generation_created)

    def _on_generation_created(self, event: Any) -> None:
        self._generation_created_emitted = True
        logger.warning("[QWEN] generation_created emitted! user_initiated=%s",
                      getattr(event, 'user_initiated', 'unknown'))

    def _fix_outgoing(self, event: dict[str, Any]) -> None:
        event_type = event.get("type", "")

        if event_type == "session.update":
            session = event.get("session", {})
            if session.get("input_audio_format") == "pcm16":
                session["input_audio_format"] = "pcm"
            if session.get("output_audio_format") == "pcm16":
                session["output_audio_format"] = "pcm"
            logger.warning("[QWEN] >>> session.update voice=%s modalities=%s audio_fmt=%s",
                          session.get("voice"), session.get("modalities"),
                          session.get("input_audio_format"))

        elif event_type == "response.create":
            resp = event.get("response", {})
            metadata = resp.get("metadata", {})
            if isinstance(metadata, dict):
                self._last_response_create_event_id = metadata.get("client_event_id")
            logger.warning("[QWEN] >>> response.create event_id=%s client_event_id=%s",
                          event.get("event_id"), self._last_response_create_event_id)

        elif event_type == "input_audio_buffer.append":
            pass  # Don't log audio data
        else:
            logger.warning("[QWEN] >>> %s", event_type)

    def _fix_incoming(self, event: dict[str, Any]) -> None:
        event_type = event.get("type", "")

        # Fix 1: Inject client_event_id
        if event_type == "response.created":
            response = event.get("response", {})
            response_id = response.get("id", "unknown")
            has_metadata = isinstance(response.get("metadata"), dict)

            if self._last_response_create_event_id:
                if not has_metadata:
                    response["metadata"] = {}
                if "client_event_id" not in response.get("metadata", {}):
                    response["metadata"]["client_event_id"] = self._last_response_create_event_id
                    logger.warning("[QWEN] <<< response.created id=%s — INJECTED client_event_id=%s",
                                  response_id, self._last_response_create_event_id)
                self._last_response_create_event_id = None
            else:
                logger.warning("[QWEN] <<< response.created id=%s — no pending event_id to inject",
                              response_id)

        # Fix 2: output_item.added
        elif event_type == "response.output_item.added":
            item = event.get("item", {})
            if "object" not in item:
                item["object"] = "realtime.item"
            logger.warning("[QWEN] <<< response.output_item.added id=%s type=%s object=%s",
                          item.get("id"), item.get("type"), item.get("object"))

        # Fix 3: content_part.added
        elif event_type == "response.content_part.added":
            part = event.get("part", {})
            if "type" not in part and "audio" in str(event):
                part["type"] = "audio"
            logger.warning("[QWEN] <<< response.content_part.added part_type=%s item_id=%s",
                          part.get("type"), event.get("item_id"))

        # Fix 4: output_item.done
        elif event_type == "response.output_item.done":
            item = event.get("item", {})
            if "object" not in item:
                item["object"] = "realtime.item"
            logger.warning("[QWEN] <<< response.output_item.done id=%s", item.get("id"))

        # Audio transcript events
        elif "audio_transcript" in event_type:
            text = event.get("delta", event.get("transcript", ""))
            logger.warning("[QWEN] <<< %s text=%s", event_type, str(text)[:80])

        # Audio delta — count chunks
        elif "audio" in event_type and "delta" in event_type:
            self._audio_chunks_received += 1
            delta = event.get("delta", "")
            logger.warning("[QWEN] <<< %s chunk #%d size=%d bytes",
                          event_type, self._audio_chunks_received, len(delta))

        # Audio done
        elif "audio" in event_type and "done" in event_type:
            logger.warning("[QWEN] <<< %s — total audio chunks received: %d",
                          event_type, self._audio_chunks_received)

        # Response done
        elif event_type == "response.done":
            response = event.get("response", {})
            usage = response.get("usage", {})
            logger.warning("[QWEN] <<< response.done — usage=%s generation_created=%s",
                          usage, self._generation_created_emitted)
            self._audio_chunks_received = 0

        # All other events
        elif event_type:
            logger.warning("[QWEN] <<< %s", event_type)

    async def _create_ws_conn(self) -> aiohttp.ClientWebSocketResponse:
        headers = {
            "User-Agent": "LiveKit Agents",
            "Authorization": f"Bearer {self._realtime_model._opts.api_key}",
        }

        url = process_base_url(
            self._realtime_model._opts.base_url,
            self._realtime_model._opts.model,
            is_azure=self._realtime_model._opts.is_azure,
            api_version=self._realtime_model._opts.api_version,
            azure_deployment=self._realtime_model._opts.azure_deployment,
        )

        logger.warning("[QWEN] Connecting to: %s", url)

        try:
            ws = await asyncio.wait_for(
                self._realtime_model._ensure_http_session().ws_connect(
                    url=url, headers=headers
                ),
                self._realtime_model._opts.conn_options.timeout,
            )
            logger.warning("[QWEN] WebSocket connected!")
            return ws
        except aiohttp.ClientError as e:
            logger.error("[QWEN] Client error: %s", e)
            raise APIConnectionError(
                "DashScope Realtime API client connection error"
            ) from e
        except asyncio.TimeoutError as e:
            logger.error("[QWEN] Connection timed out")
            raise APIConnectionError(
                message="DashScope Realtime API connection timed out",
            ) from e


class RealtimeModel(OpenAIRealtimeModel):
    """Qwen-Omni-Realtime via DashScope."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        voice: str = DEFAULT_VOICE,
        api_key: Optional[str] = None,
        region: str = "intl",
        temperature: float = 0.7,
        conn_options: APIConnectOptions = APIConnectOptions(
            max_retry=3, retry_interval=2.0, timeout=30.0
        ),
        **kwargs,
    ) -> None:
        resolved_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not resolved_key:
            raise ValueError(
                "DashScope API key is required. "
                "Pass api_key or set the DASHSCOPE_API_KEY environment variable."
            )

        base_endpoint = (
            DASHSCOPE_INTL_BASE_URL if region == "intl" else DASHSCOPE_CN_BASE_URL
        )
        base_url = f"{base_endpoint}?model={model}"

        logger.warning("[QWEN] Init: model=%s voice=%s region=%s", model, voice, region)

        super().__init__(
            model=model,
            voice=voice,
            api_key=resolved_key,
            base_url=base_url,
            temperature=temperature,
            conn_options=conn_options,
            **kwargs,
        )

        self._opts.is_azure = True

    @property
    def provider(self) -> str:
        return "qwen"

    def session(self) -> QwenRealtimeSession:
        sess = QwenRealtimeSession(self)
        self._sessions.add(sess)
        return sess
