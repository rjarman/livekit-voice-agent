"""
Qwen-Omni-Realtime plugin for LiveKit Agents.

DashScope's Realtime WebSocket API is OpenAI-compatible in event format,
so we reuse the OpenAI RealtimeModel with a custom base_url pointing to
DashScope's Singapore endpoint.

This gives us full compatibility with LiveKit's agent framework —
same tools, same events, same session management — just routed through
Alibaba Cloud instead of OpenAI.

Supported models (from DashScope Singapore):
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
from livekit.plugins.openai.realtime import RealtimeModel as OpenAIRealtimeModel

logger = logging.getLogger("livekit.plugins.qwen")

# DashScope International (Singapore) endpoint for Realtime WebSocket
# The OpenAI plugin constructs the WS URL from base_url by appending /realtime
# DashScope expects: wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime
# So we set base_url to the HTTP equivalent and let the plugin convert it
DASHSCOPE_INTL_BASE_URL = "https://dashscope-intl.aliyuncs.com/api-ws/v1/realtime"
DASHSCOPE_CN_BASE_URL = "https://dashscope.aliyuncs.com/api-ws/v1/realtime"

# Default model — fastest option for low latency from South Asia
DEFAULT_MODEL = "qwen-omni-turbo-realtime"
DEFAULT_VOICE = "Cherry"


class RealtimeModel(OpenAIRealtimeModel):
    """Qwen-Omni-Realtime via DashScope, compatible with LiveKit's OpenAI Realtime plugin.

    Since DashScope's Realtime API uses the same WebSocket protocol as OpenAI
    (same event types: session.update, input_audio_buffer.append, response.audio.delta, etc.),
    we extend the OpenAI RealtimeModel and override the connection parameters.

    Args:
        model: Qwen realtime model name. Default: "qwen-omni-turbo-realtime"
        voice: Voice name. Default: "Cherry". Options: Cherry, Ethan, Tina, etc.
        api_key: DashScope API key. Defaults to DASHSCOPE_API_KEY env var.
        region: "intl" (Singapore) or "cn" (Beijing). Default: "intl"
        temperature: Sampling temperature. Default: 0.7
        instructions: System prompt for the model.
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

        base_url = DASHSCOPE_INTL_BASE_URL if region == "intl" else DASHSCOPE_CN_BASE_URL

        logger.info(
            "Initializing Qwen RealtimeModel: model=%s, voice=%s, region=%s, base_url=%s",
            model, voice, region, base_url,
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

    @property
    def provider(self) -> str:
        return "qwen"
