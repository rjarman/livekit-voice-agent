"""
Qwen-Omni-Realtime plugin for LiveKit Agents.

Handles DashScope protocol differences from OpenAI:
    1. Event names: same as Azure (older format) — is_azure=True
    2. Auth: Bearer token (not Azure's api-key header)
    3. Audio format: "pcm" (not "pcm16")
    4. Metadata: DashScope doesn't echo response.create metadata —
       we inject client_event_id to resolve generate_reply futures

Supported models:
    - qwen-omni-turbo-realtime
    - qwen-omni-plus-realtime
    - qwen3-omni-flash-realtime
    - qwen3.5-omni-flash-realtime
    - qwen3.5-omni-plus-realtime

Usage:
    from livekit.plugins.qwen import RealtimeModel
    model = RealtimeModel(model="qwen-omni-turbo-realtime", voice="Cherry")
    session = AgentSession(llm=model, vad=vad)
"""

import asyncio
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
    """Session with DashScope-specific fixes."""

    def __init__(self, realtime_model: "RealtimeModel") -> None:
        super().__init__(realtime_model)
        self._last_response_create_event_id: str | None = None
        # Fix outgoing events
        self.on("openai_client_event_queued", self._fix_outgoing)
        # Fix incoming events
        self.on("openai_server_event_received", self._fix_incoming)

    def _fix_outgoing(self, event: dict[str, Any]) -> None:
        """Fix outgoing events for DashScope compatibility."""
        event_type = event.get("type", "")

        # Fix audio format: Azure sends "pcm16", DashScope expects "pcm"
        if event_type == "session.update":
            session = event.get("session", {})
            if session.get("input_audio_format") == "pcm16":
                session["input_audio_format"] = "pcm"
            if session.get("output_audio_format") == "pcm16":
                session["output_audio_format"] = "pcm"

        # Track response.create event_id for metadata injection
        elif event_type == "response.create":
            resp = event.get("response", {})
            metadata = resp.get("metadata", {})
            if isinstance(metadata, dict):
                self._last_response_create_event_id = metadata.get("client_event_id")

    def _fix_incoming(self, event: dict[str, Any]) -> None:
        """Fix incoming events for DashScope compatibility."""
        event_type = event.get("type", "")

        # DashScope doesn't echo metadata from response.create.
        # The OpenAI plugin needs client_event_id in response.created
        # to resolve generate_reply futures. We inject it.
        if event_type == "response.created" and self._last_response_create_event_id:
            response = event.get("response", {})
            if not isinstance(response.get("metadata"), dict):
                response["metadata"] = {}
            if "client_event_id" not in response["metadata"]:
                response["metadata"]["client_event_id"] = self._last_response_create_event_id
                logger.info("[QWEN] Injected client_event_id into response.created")
            self._last_response_create_event_id = None

    async def _create_ws_conn(self) -> aiohttp.ClientWebSocketResponse:
        """Use Bearer auth (not Azure's api-key header)."""
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
            raise APIConnectionError(
                "DashScope Realtime API client connection error"
            ) from e
        except asyncio.TimeoutError as e:
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

        logger.info(
            "Initializing Qwen RealtimeModel: model=%s, voice=%s, region=%s",
            model, voice, region,
        )

        super().__init__(
            model=model,
            voice=voice,
            api_key=resolved_key,
            base_url=base_url,
            temperature=temperature,
            conn_options=conn_options,
            **kwargs,
        )

        # Enable Azure event name mapping (DashScope uses same older names)
        self._opts.is_azure = True

    @property
    def provider(self) -> str:
        return "qwen"

    def session(self) -> QwenRealtimeSession:
        sess = QwenRealtimeSession(self)
        self._sessions.add(sess)
        return sess
