"""
Apple Seller Voice Agent for LiveKit.

Sells Apple products via voice: recommends products, fetches latest prices,
and triggers n8n workflow for purchase on user command.
"""

import asyncio
import logging
import os
from typing import Any

import aiohttp
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    WorkerOptions,
    cli,
    AutoSubscribe,
    function_tool,
)
from livekit.plugins import assemblyai, cartesia, groq, silero

load_dotenv()

logger = logging.getLogger("apple-seller-agent")
logger.setLevel(logging.INFO)

# n8n webhook URLs from env (optional)
N8N_PURCHASE_WEBHOOK_URL = os.getenv("N8N_PURCHASE_WEBHOOK_URL", "").strip()
N8N_PRICES_WEBHOOK_URL = os.getenv("N8N_PRICES_WEBHOOK_URL", "").strip()

# Delay before speaking a "one moment" message during slow tool calls (seconds)
TOOL_STATUS_UPDATE_DELAY = 0.6

# Fallback catalog of Apple products with representative prices (USD)
# When N8N_PRICES_WEBHOOK_URL is set, fetched prices override or extend this.
APPLE_PRODUCT_CATALOG: list[dict[str, Any]] = [
    {"id": "iphone-16", "name": "iPhone 16", "category": "iPhone", "price_usd": 799, "description": "6.1-inch, 128GB"},
    {"id": "iphone-16-plus", "name": "iPhone 16 Plus", "category": "iPhone", "price_usd": 899, "description": "6.7-inch, 128GB"},
    {"id": "iphone-16-pro", "name": "iPhone 16 Pro", "category": "iPhone", "price_usd": 999, "description": "6.3-inch, 256GB"},
    {"id": "iphone-16-pro-max", "name": "iPhone 16 Pro Max", "category": "iPhone", "price_usd": 1199, "description": "6.9-inch, 256GB"},
    {"id": "ipad", "name": "iPad", "category": "iPad", "price_usd": 349, "description": "10.9-inch, 64GB Wi-Fi"},
    {"id": "ipad-air-11", "name": "iPad Air 11-inch", "category": "iPad", "price_usd": 599, "description": "M2 chip, 128GB"},
    {"id": "ipad-air-13", "name": "iPad Air 13-inch", "category": "iPad", "price_usd": 799, "description": "M2 chip, 128GB"},
    {"id": "ipad-pro-11", "name": "iPad Pro 11-inch", "category": "iPad", "price_usd": 999, "description": "M4 chip, 256GB"},
    {"id": "ipad-pro-13", "name": "iPad Pro 13-inch", "category": "iPad", "price_usd": 1299, "description": "M4 chip, 256GB"},
    {"id": "macbook-air-m3", "name": "MacBook Air 13-inch M3", "category": "Mac", "price_usd": 1099, "description": "8GB RAM, 256GB SSD"},
    {"id": "macbook-air-m3-15", "name": "MacBook Air 15-inch M3", "category": "Mac", "price_usd": 1299, "description": "8GB RAM, 256GB SSD"},
    {"id": "macbook-pro-14", "name": "MacBook Pro 14-inch M4 Pro", "category": "Mac", "price_usd": 1599, "description": "18GB RAM, 512GB SSD"},
    {"id": "macbook-pro-16", "name": "MacBook Pro 16-inch M4 Pro", "category": "Mac", "price_usd": 2499, "description": "18GB RAM, 512GB SSD"},
    {"id": "airpods-3", "name": "AirPods (3rd gen)", "category": "Accessories", "price_usd": 169, "description": "MagSafe Charging Case"},
    {"id": "airpods-pro-2", "name": "AirPods Pro (2nd gen)", "category": "Accessories", "price_usd": 249, "description": "Active Noise Cancellation"},
    {"id": "airpods-max", "name": "AirPods Max", "category": "Accessories", "price_usd": 549, "description": "Over-ear, Spatial Audio"},
    {"id": "apple-watch-se", "name": "Apple Watch SE", "category": "Watch", "price_usd": 249, "description": "40mm or 44mm GPS"},
    {"id": "apple-watch-series-10", "name": "Apple Watch Series 10", "category": "Watch", "price_usd": 399, "description": "41mm or 45mm GPS"},
    {"id": "apple-watch-ultra-2", "name": "Apple Watch Ultra 2", "category": "Watch", "price_usd": 799, "description": "49mm Titanium"},
]


async def _fetch_prices_from_webhook() -> list[dict[str, Any]]:
    """Fetch latest prices from n8n webhook if configured."""
    if not N8N_PRICES_WEBHOOK_URL:
        return []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(N8N_PRICES_WEBHOOK_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    logger.warning("Prices webhook returned status %s", resp.status)
                    return []
                data = await resp.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "products" in data:
                    return data["products"]
                return []
    except Exception as e:
        logger.warning("Failed to fetch prices from webhook: %s", e)
        return []


async def _trigger_n8n_purchase(
    product_id: str, product_name: str, quantity: int, user_name: str = ""
) -> dict[str, Any]:
    """POST to n8n purchase webhook."""
    if not N8N_PURCHASE_WEBHOOK_URL:
        return {"success": False, "error": "Purchase webhook not configured. Set N8N_PURCHASE_WEBHOOK_URL."}
    payload = {
        "product_id": product_id,
        "product_name": product_name,
        "quantity": quantity,
        "user_name": (user_name or "").strip(),
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                N8N_PURCHASE_WEBHOOK_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    return {"success": False, "error": f"Webhook returned {resp.status}", "body": text}
                try:
                    return {"success": True, "response": await resp.json() if resp.content_type == "application/json" else text}
                except Exception:
                    return {"success": True, "response": text}
    except Exception as e:
        logger.exception("Purchase webhook request failed")
        return {"success": False, "error": str(e)}


class AppleSellerAgent(Agent):
    """Voice agent that sells Apple products and can trigger n8n purchase workflow."""

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a friendly Apple product seller in a voice call. The user is talking to you via voice.
Your job is to help them find the right Apple product (iPhone, iPad, Mac, AirPods, Apple Watch, etc.) and complete a purchase if they want.

- Be concise and clear. No emojis, asterisks, or complex formatting in your speech.
- CRITICAL: Never say, speak, or output any internal function or tool name (e.g. get_apple_prices, trigger_purchase, or any other technical name). Only speak natural sentences to the user. When you need to fetch prices or place an order, call the tool silently and then say the result in plain language (e.g. "Here are our iPhones..." or "Your order is confirmed").
- When the user asks for prices or "what do you have", call the price lookup tool (with category or search_term if relevant) and then summarize the results in a short, natural reply. Do not announce that you are calling a function.
- When the user wants to buy something, ask for their name if needed, then call the purchase tool and confirm in natural language. Do not say any tool name.
- If the user is unsure, suggest a few options. Always use the tools for real prices and orders; do not make up prices or order IDs."""
        )

    @function_tool()
    async def get_apple_prices(
        self,
        context: RunContext,
        category: str = "",
        search_term: str = "",
    ) -> dict[str, Any]:
        """Get latest Apple product prices. Use when the user asks for prices, what products are available, or what you sell.
        Args:
            category: Filter by category: iPhone, iPad, Mac, Accessories, Watch. Leave empty for all.
            search_term: Optional search in product names (e.g. 'pro', 'air', 'macbook').
        """
        # If we will call the external API, say "one moment" after a short delay so user doesn't hear silence
        async def _speak_fetching_prices() -> None:
            await asyncio.sleep(TOOL_STATUS_UPDATE_DELAY)
            await context.session.generate_reply(
                instructions="Say one very short sentence: you are checking the latest prices, one moment. No lists or details."
            )

        fetch_task: asyncio.Task[list[dict[str, Any]]] | None = None
        if N8N_PRICES_WEBHOOK_URL:
            status_task = asyncio.create_task(_speak_fetching_prices())
            fetch_task = asyncio.create_task(_fetch_prices_from_webhook())
            try:
                products = await fetch_task
            finally:
                status_task.cancel()
                try:
                    await status_task
                except asyncio.CancelledError:
                    pass
        else:
            products = []

        if not products:
            products = [p.copy() for p in APPLE_PRODUCT_CATALOG]

        category_clean = category.strip().lower() if category else ""
        search_clean = search_term.strip().lower() if search_term else ""

        if category_clean:
            products = [p for p in products if (p.get("category") or "").lower() == category_clean]
        if search_clean:
            products = [
                p for p in products
                if search_clean in (p.get("name") or "").lower() or search_clean in (p.get("id") or "").lower()
            ]

        if not products:
            return {"products": [], "message": "No products match. Try another category or search."}

        return {
            "products": [
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "category": p.get("category"),
                    "price_usd": p.get("price_usd"),
                    "description": p.get("description"),
                }
                for p in products
            ],
            "message": f"Found {len(products)} product(s).",
        }

    @function_tool()
    async def trigger_purchase(
        self,
        context: RunContext,
        product_id: str,
        quantity: int = 1,
        user_name: str = "",
    ) -> dict[str, Any]:
        """Trigger the n8n purchase workflow so the user can complete the order. Call this when the user confirms they want to buy and has given their name for the order.
        Args:
            product_id: The product id from get_apple_prices (e.g. iphone-16, airpods-pro-2).
            quantity: Number of units to order (default 1).
            user_name: The name of the customer placing the order (ask for it before calling if not yet provided).
        """
        name = next((p["name"] for p in APPLE_PRODUCT_CATALOG if p.get("id") == product_id), product_id)

        async def _speak_processing_order() -> None:
            await asyncio.sleep(TOOL_STATUS_UPDATE_DELAY)
            await context.session.generate_reply(
                instructions="Say one very short sentence: processing your order, one moment. No lists or details."
            )

        if N8N_PURCHASE_WEBHOOK_URL:
            status_task = asyncio.create_task(_speak_processing_order())
            try:
                result = await _trigger_n8n_purchase(product_id, name, quantity, user_name)
            finally:
                status_task.cancel()
                try:
                    await status_task
                except asyncio.CancelledError:
                    pass
            return result
        result = await _trigger_n8n_purchase(product_id, name, quantity, user_name)
        return result


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext) -> None:
    room_name = ctx.room.name
    logger.info("Apple seller agent connecting to room: %s", room_name)

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    logger.info("Apple seller agent connected to room: %s", room_name)

    session = AgentSession(
        stt=assemblyai.STT(),
        llm=groq.LLM(model="llama-3.1-8b-instant"),
        tts=cartesia.TTS(),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        agent=AppleSellerAgent(),
        room=ctx.room,
    )

    logger.info("Apple seller session started in room: %s", room_name)
    await session.say("Hi! I'm your Apple sales assistant. I can show you our latest products and prices, or help you place an order. What are you looking for?")
    logger.info("Greeting sent, session running...")

    disconnect_event = asyncio.Event()

    async def on_shutdown() -> None:
        disconnect_event.set()

    ctx.add_shutdown_callback(on_shutdown)
    await disconnect_event.wait()
    logger.info("Apple seller agent leaving room: %s", room_name)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="apple-seller-agent",
        ),
    )
