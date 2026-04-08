"""
Qwen-Omni-Realtime plugin for LiveKit Agents.

Handles DashScope protocol differences from OpenAI.
Supports both qwen-omni-turbo-realtime and qwen3.5-omni-* models.
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

# Fields accepted by DashScope session.update (turbo models)
_TURBO_ALLOWED_FIELDS = {
    "modalities", "voice", "instructions", "input_audio_format",
    "output_audio_format", "turn_detection",
    "enable_search", "search_options",
}

# qwen3/qwen3.5 models are stricter — only these fields are safe.
# turn_detection causes immediate disconnect on qwen3+ models;
# the server uses its own VAD by default.
_QWEN3_ALLOWED_FIELDS = {
    "modalities", "voice", "instructions",
    "input_audio_format", "output_audio_format",
}


class QwenRealtimeSession(OpenAIRealtimeSession):
    """Session with DashScope-specific fixes and debug logging."""

    def __init__(self, realtime_model: "RealtimeModel") -> None:
        super().__init__(realtime_model)
        self._last_response_create_event_id: str | None = None
        self._audio_chunks_received = 0
        self._generation_created_emitted = False
        self._model_name: str = realtime_model._opts.model
        self._is_qwen3: bool = "qwen3" in self._model_name
        self.on("openai_client_event_queued", self._fix_outgoing)
        self.on("openai_server_event_received", self._fix_incoming)
        self.on("generation_created", self._on_generation_created)

    def _on_generation_created(self, event: Any) -> None:
        self._generation_created_emitted = True
        logger.info("[QWEN] generation_created emitted! user_initiated=%s",
                    getattr(event, 'user_initiated', 'unknown'))

    def _fix_outgoing(self, event: dict[str, Any]) -> None:
        event_type = event.get("type", "")

        if event_type == "session.update":
            session = event.get("session", {})

            # DashScope requires "pcm", not "pcm16" (Azure default)
            session["input_audio_format"] = "pcm"
            session["output_audio_format"] = "pcm"

            # Pick allowed fields based on model family
            allowed = _QWEN3_ALLOWED_FIELDS if self._is_qwen3 else _TURBO_ALLOWED_FIELDS

            # Remove disallowed or None-valued fields
            keys_to_remove = [
                k for k in session
                if k not in allowed or session[k] is None
            ]
            for k in keys_to_remove:
                del session[k]

            # Ensure audio modalities when voice is present
            if "modalities" in session or "voice" in session:
                session.setdefault("modalities", ["text", "audio"])

            # Clean up turn_detection for turbo models (strip unsupported sub-fields)
            if not self._is_qwen3:
                td = session.get("turn_detection")
                if td is not None and isinstance(td, dict):
                    session["turn_detection"] = {
                        "type": "server_vad",
                        "threshold": td.get("threshold", 0.5),
                        "silence_duration_ms": td.get("silence_duration_ms", 800),
                    }
                elif td is None and "turn_detection" in session:
                    del session["turn_detection"]

            # Log full event JSON for debugging
            logger.info("[QWEN] >>> session.update FULL: %s",
                        json.dumps({"session": session}, ensure_ascii=False)[:2000])

        elif event_type == "response.create":
            # Track client_event_id before stripping
            resp = event.get("response", {})
            metadata = resp.get("metadata", {}) if isinstance(resp, dict) else {}
            if isinstance(metadata, dict):
                self._last_response_create_event_id = metadata.get("client_event_id")

            # DashScope response.create only supports type + event_id.
            # The "response" object causes text-only fallback.
            if "response" in event:
                del event["response"]

            logger.info("[QWEN] >>> response.create (stripped response obj) event_id=%s",
                        event.get("event_id"))

        elif event_type == "input_audio_buffer.append":
            # Resample 24kHz → 16kHz for DashScope (expects 16kHz input)
            import base64
            import struct
            audio_b64 = event.get("audio", "")
            if audio_b64:
                raw = base64.b64decode(audio_b64)
                # Simple 3:2 downsampling (24kHz → 16kHz)
                samples = struct.unpack(f"<{len(raw)//2}h", raw)
                resampled = []
                for i in range(0, len(samples) - 2, 3):
                    resampled.append(samples[i])
                    resampled.append((samples[i+1] + samples[i+2]) // 2)
                resampled_bytes = struct.pack(f"<{len(resampled)}h", *resampled)
                event["audio"] = base64.b64encode(resampled_bytes).decode()

            if not hasattr(self, '_audio_send_count'):
                self._audio_send_count = 0
            self._audio_send_count += 1
            if self._audio_send_count <= 3 or self._audio_send_count % 100 == 0:
                logger.debug("[QWEN] >>> input_audio_buffer.append #%d size=%d (resampled 24k→16k)",
                             self._audio_send_count, len(event.get("audio", "")))
        else:
            logger.debug("[QWEN] >>> %s", event_type)

    def _fix_incoming(self, event: dict[str, Any]) -> None:
        event_type = event.get("type", "")

        if event_type == "response.created":
            response = event.get("response", {})
            response_id = response.get("id", "unknown")

            if self._last_response_create_event_id:
                if not isinstance(response.get("metadata"), dict):
                    response["metadata"] = {}
                if "client_event_id" not in response.get("metadata", {}):
                    response["metadata"]["client_event_id"] = self._last_response_create_event_id
                    logger.info("[QWEN] <<< response.created id=%s — injected client_event_id=%s",
                                response_id, self._last_response_create_event_id)
                self._last_response_create_event_id = None
            else:
                logger.info("[QWEN] <<< response.created id=%s", response_id)

        elif event_type == "response.output_item.added":
            item = event.get("item", {})
            if "object" not in item:
                item["object"] = "realtime.item"
            logger.debug("[QWEN] <<< response.output_item.added id=%s type=%s",
                         item.get("id"), item.get("type"))

        elif event_type == "response.content_part.added":
            part = event.get("part", {})
            if "type" not in part and "audio" in str(event):
                part["type"] = "audio"
            logger.debug("[QWEN] <<< response.content_part.added part_type=%s",
                         part.get("type"))

        elif event_type == "response.output_item.done":
            item = event.get("item", {})
            if "object" not in item:
                item["object"] = "realtime.item"

        elif "audio_transcript" in event_type:
            text = event.get("delta", event.get("transcript", ""))
            logger.info("[QWEN] <<< %s text=%s", event_type, str(text)[:80])

        elif "audio" in event_type and "delta" in event_type:
            self._audio_chunks_received += 1
            if self._audio_chunks_received <= 3 or self._audio_chunks_received % 50 == 0:
                logger.debug("[QWEN] <<< %s chunk #%d", event_type, self._audio_chunks_received)

        elif event_type == "response.done":
            response = event.get("response", {})
            usage = response.get("usage", {})
            logger.info("[QWEN] <<< response.done — usage=%s audio_chunks=%d",
                        usage, self._audio_chunks_received)
            self._audio_chunks_received = 0

        elif event_type == "error":
            logger.error("[QWEN] <<< ERROR: %s", json.dumps(event, ensure_ascii=False))

        elif event_type:
            logger.debug("[QWEN] <<< %s", event_type)

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

        logger.info("[QWEN] Connecting to: %s (model=%s, is_qwen35=%s)",
                    url, self._model_name, self._is_qwen3)

        try:
            ws = await asyncio.wait_for(
                self._realtime_model._ensure_http_session().ws_connect(
                    url=url, headers=headers
                ),
                self._realtime_model._opts.conn_options.timeout,
            )
            logger.info("[QWEN] WebSocket connected!")
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

        logger.info("[QWEN] Init: model=%s voice=%s region=%s is_qwen3=%s",
                    model, voice, region, "qwen3" in model)

        super().__init__(
            model=model,
            voice=voice,
            api_key=resolved_key,
            base_url=base_url,
            temperature=temperature,
            conn_options=conn_options,
            **kwargs,
        )

        # Azure mode prevents the OpenAI plugin from appending /realtime?model=
        # to our already-complete URL, and uses the flat session format that
        # DashScope expects.
        self._opts.is_azure = True

    @property
    def provider(self) -> str:
        return "qwen"

    def session(self) -> QwenRealtimeSession:
        sess = QwenRealtimeSession(self)
        self._sessions.add(sess)
        return sess
