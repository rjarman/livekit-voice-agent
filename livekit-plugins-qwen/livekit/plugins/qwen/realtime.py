"""
Qwen-Omni-Realtime plugin for LiveKit Agents.

DashScope's Realtime WebSocket API uses older event names (same as Azure OpenAI):
    - response.audio.delta (not response.output_audio.delta)
    - response.audio_transcript.delta (not response.output_audio_transcript.delta)
    - conversation.item.created (not conversation.item.added)

We extend the OpenAI plugin, set is_azure=True for event mapping,
embed the model in the URL, and fix the auth header to use Bearer token
(DashScope uses Bearer auth, not Azure's api-key header).

Supported models:
    - qwen-omni-turbo-realtime           (fastest, good quality)
    - qwen-omni-plus-realtime            (better quality, slower)
    - qwen3-omni-flash-realtime          (fast, good)
    - qwen3.5-omni-flash-realtime        (newest fast)
    - qwen3.5-omni-plus-realtime         (newest best quality)

Voices: Cherry, Ethan, Tina, and 52 more (see DashScope docs)

Usage:
    from livekit.plugins.qwen import RealtimeModel

    model = RealtimeModel(
        model="qwen-omni-turbo-realtime",
        voice="Cherry",
    )

    session = AgentSession(llm=model, vad=vad)
"""

import logging
import os
from typing import Optional

from livekit.agents import APIConnectOptions
from livekit.plugins.openai.realtime import (
    RealtimeModel as OpenAIRealtimeModel,
    RealtimeSession as OpenAIRealtimeSession,
)

logger = logging.getLogger("livekit.plugins.qwen")

# DashScope Realtime WebSocket endpoints
DASHSCOPE_INTL_BASE_URL = "https://dashscope-intl.aliyuncs.com/api-ws/v1/realtime"
DASHSCOPE_CN_BASE_URL = "https://dashscope.aliyuncs.com/api-ws/v1/realtime"

DEFAULT_MODEL = "qwen-omni-turbo-realtime"
DEFAULT_VOICE = "Cherry"


class RealtimeModel(OpenAIRealtimeModel):
    """Qwen-Omni-Realtime via DashScope, compatible with LiveKit's OpenAI Realtime plugin.

    Args:
        model: Qwen realtime model name. Default: "qwen-omni-turbo-realtime"
        voice: Voice name. Default: "Cherry". Options: Cherry, Ethan, Tina, etc.
        api_key: DashScope API key. Defaults to DASHSCOPE_API_KEY env var.
        region: "intl" (Singapore) or "cn" (Beijing). Default: "intl"
        temperature: Sampling temperature. Default: 0.7
        conn_options: Connection options (timeout, retries).
    """

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

        base_endpoint = DASHSCOPE_INTL_BASE_URL if region == "intl" else DASHSCOPE_CN_BASE_URL
        # Embed model in the base URL so Azure-mode URL construction preserves it
        base_url = f"{base_endpoint}?model={model}"

        logger.info(
            "Initializing Qwen RealtimeModel: model=%s, voice=%s, region=%s",
            model, voice, region,
        )

        # Store the key for our custom auth header
        self._dashscope_api_key = resolved_key

        super().__init__(
            model=model,
            voice=voice,
            api_key=resolved_key,
            base_url=base_url,
            temperature=temperature,
            conn_options=conn_options,
            **kwargs,
        )

        # Enable Azure event name mapping (DashScope uses the same older names).
        # This must be set AFTER super().__init__ so the URL is built correctly first.
        self._opts.is_azure = True

    @property
    def provider(self) -> str:
        return "qwen"

    def session(self):
        """Create a session that uses Bearer auth instead of Azure's api-key header."""
        sess = super().session()
        # Monkey-patch the _create_ws_conn method to fix the auth header.
        # The OpenAI plugin sends "api-key: <key>" in Azure mode,
        # but DashScope expects "Authorization: Bearer <key>".
        original_create_ws = sess._create_ws_conn

        async def _patched_create_ws_conn():
            import asyncio
            import aiohttp
            from livekit.agents._exceptions import APIConnectionError
            from livekit.plugins.openai.realtime.realtime_model import process_base_url

            headers = {
                "User-Agent": "LiveKit Agents",
                "Authorization": f"Bearer {self._dashscope_api_key}",
            }

            url = process_base_url(
                self._opts.base_url,
                self._opts.model,
                is_azure=self._opts.is_azure,
                api_version=self._opts.api_version,
                azure_deployment=self._opts.azure_deployment,
            )

            logger.debug("Connecting to DashScope Realtime: %s", url)

            try:
                return await asyncio.wait_for(
                    self._ensure_http_session().ws_connect(url=url, headers=headers),
                    self._opts.conn_options.timeout,
                )
            except aiohttp.ClientError as e:
                raise APIConnectionError("DashScope Realtime API client connection error") from e
            except asyncio.TimeoutError as e:
                raise APIConnectionError("DashScope Realtime API connection timed out") from e

        sess._create_ws_conn = _patched_create_ws_conn
        return sess
