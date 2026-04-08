"""
Qwen-Omni-Realtime plugin for LiveKit Agents.

DashScope differences from OpenAI/Azure:
    1. Event names: same as Azure (older format) — handled by is_azure=True
    2. Auth: Bearer token (not Azure's api-key header)
    3. Audio format: "pcm" (not "pcm16")
    4. URL: DashScope Singapore endpoint with ?model= parameter

Supported models:
    - qwen-omni-turbo-realtime
    - qwen-omni-plus-realtime
    - qwen3-omni-flash-realtime
    - qwen3.5-omni-flash-realtime
    - qwen3.5-omni-plus-realtime

Voices: Cherry, Ethan, Tina, and 52 more

Usage:
    from livekit.plugins.qwen import RealtimeModel

    model = RealtimeModel(
        model="qwen-omni-turbo-realtime",
        voice="Cherry",
    )
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


def _fix_dashscope_event(event: dict[str, Any]) -> None:
    """In-place fix of outgoing events for DashScope compatibility.

    DashScope expects "pcm" audio format, Azure sends "pcm16".
    """
    if event.get("type") == "session.update":
        session = event.get("session", {})
        if session.get("input_audio_format") == "pcm16":
            session["input_audio_format"] = "pcm"
        if session.get("output_audio_format") == "pcm16":
            session["output_audio_format"] = "pcm"


class QwenRealtimeSession(OpenAIRealtimeSession):
    """Session with DashScope-specific auth and audio format handling."""

    def __init__(self, realtime_model: "RealtimeModel") -> None:
        super().__init__(realtime_model)
        # Listen to outgoing events and fix format before they're sent
        self.on("openai_client_event_queued", _fix_dashscope_event)

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

        logger.info("[QWEN] Connecting to: %s", url)

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
        """Create a QwenRealtimeSession with correct auth and format handling."""
        sess = QwenRealtimeSession(self)
        self._sessions.add(sess)
        return sess
