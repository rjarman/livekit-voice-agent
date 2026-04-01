"""
Apple Seller Voice Agent (Bengali) for LiveKit.

Same functionality as the English agent, but all spoken conversation is in Bengali.
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
from livekit.plugins import cartesia, google, groq, openai, silero, assemblyai

# ---------------------------------------------------------------------------
# Bengali agent provider stack (all Google):
#   STT: Google Cloud Speech-to-Text  (bn-IN, requires GOOGLE_APPLICATION_CREDENTIALS)
#   LLM: Gemini 2.5 Flash             (GOOGLE_API_KEY)
#   TTS: Google Cloud Text-to-Speech   (bn-IN Wavenet, same creds as STT)
# ---------------------------------------------------------------------------

load_dotenv()

logger = logging.getLogger("apple-seller-agent-bn")
logger.setLevel(logging.INFO)

# n8n webhook URLs from env (optional)
N8N_PURCHASE_WEBHOOK_URL = os.getenv("N8N_PURCHASE_WEBHOOK_URL", "").strip()
N8N_PRICES_WEBHOOK_URL = os.getenv("N8N_PRICES_WEBHOOK_URL", "").strip()

logger.info(
    "Webhook config — purchase: %s, prices: %s",
    N8N_PURCHASE_WEBHOOK_URL or "(NOT SET)",
    N8N_PRICES_WEBHOOK_URL or "(NOT SET)",
)

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


def _normalize_products_response(raw: list[Any]) -> list[dict[str, Any]]:
    """Flatten n8n response: handle nested structure like [{ data: { data: { products: [...] } } }]."""
    if not raw or not isinstance(raw, list):
        return []
    # Single wrapper object with nested data.data.products (common n8n Firecrawl shape)
    if len(raw) == 1 and isinstance(raw[0], dict):
        inner = raw[0]
        if isinstance(inner.get("data"), dict) and isinstance(inner["data"].get("data"), dict):
            nested = inner["data"]["data"].get("products")
            if isinstance(nested, list) and nested:
                return [p for p in nested if isinstance(p, dict)]
    # Already a list of product objects (have id/name/price_usd)
    if all(isinstance(p, dict) and (p.get("id") is not None or p.get("name")) for p in raw):
        return list(raw)
    # Multiple wrappers: collect all data.data.products
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        data = item.get("data")
        if isinstance(data, dict) and isinstance(data.get("data"), dict):
            for p in data["data"].get("products") or []:
                if isinstance(p, dict):
                    out.append(p)
    return out if out else list(raw)


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
                logger.info("Prices webhook raw response type=%s len=%s", type(data).__name__, len(data) if isinstance(data, (list, dict)) else "n/a")
                if isinstance(data, list):
                    out = _normalize_products_response(data)
                    logger.info("Prices webhook normalized list -> %d products", len(out))
                    return out
                if isinstance(data, dict) and "products" in data:
                    out = _normalize_products_response(data["products"])
                    logger.info("Prices webhook normalized dict.products -> %d products", len(out))
                    return out
                logger.warning("Prices webhook unexpected shape: no list or dict.products")
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
    logger.info("POSTing to purchase webhook: %s with payload: %s", N8N_PURCHASE_WEBHOOK_URL, payload)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                N8N_PURCHASE_WEBHOOK_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                text = await resp.text()
                logger.info("Purchase webhook response: status=%s body=%s", resp.status, text[:500])
                if resp.status >= 400:
                    return {"success": False, "error": f"Webhook returned {resp.status}", "body": text}
                try:
                    return {"success": True, "response": await resp.json() if resp.content_type == "application/json" else text}
                except Exception:
                    return {"success": True, "response": text}
    except Exception as e:
        logger.exception("Purchase webhook request failed")
        return {"success": False, "error": str(e)}


class AppleSellerAgentBn(Agent):
    """Bengali voice agent that sells Apple products and can trigger n8n purchase workflow."""

    # Delay after goodbye before actually disconnecting, so TTS finishes speaking
    END_CALL_DELAY = 2.0

    def __init__(self, disconnect_event: asyncio.Event) -> None:
        self._disconnect_event = disconnect_event
        # NOTE: System prompt is in English with explicit "reply in Bengali" instruction.
        # This works MUCH better than writing the entire prompt in Bengali because:
        # 1. LLMs follow English instructions more reliably (stronger instruction tuning)
        # 2. Bengali-only prompts often cause the model to mix languages or ignore rules
        # 3. The model still generates Bengali output because rule #1 explicitly requires it
        super().__init__(
            instructions="""\
You are a friendly Apple product seller on a voice call. The customer speaks Bengali (Bangla). \
You MUST reply ONLY in natural, spoken Bengali. Every word you speak must be Bengali, \
except product names like "iPhone", "MacBook", "AirPods" which stay in English.

RULES:
1. Speak ONLY natural, short Bengali sentences. This is a phone call. Keep each reply to 2-3 sentences MAX. Never give long explanations.
2. NEVER say any function name, variable, parameter, JSON key, or code-like word out loud. \
Forbidden: "get_apple_prices", "trigger_purchase", "product_id", "price_usd". \
CRITICAL: Never write digits like 799 or ৭৯৯. Always spell out numbers as Bengali words. \
Example: $799 must be said as "saat shoh nirannobboi dollar", $1,199 as "egaro shoh nirannobboi dollar". \
This is a voice call — the listener cannot read digits.
3. NEVER narrate your internal actions. Do NOT say "ami daam dekhchi" or "ami tool call korchi". \
Just do it silently, then speak the result naturally.
4. When a customer asks about ANY product by name or type, you MUST call the price lookup tool first. \
Never say a product is unavailable without checking the catalog.
5. List at most 3 products at a time. Ask if they want to hear more.
6. To purchase: ask for the customer's name (if unknown), confirm the product and quantity in Bengali, then place the order.
7. Never guess prices. Always use the tool.
8. No emoji, no asterisks, no bullet points, no markdown. Plain spoken Bengali only.
9. After a successful order or when the customer wants to end, say a brief goodbye in Bengali, then end the call. \
Always say goodbye BEFORE ending so the customer hears it."""
        )

    @function_tool()
    async def get_apple_prices(
        self,
        context: RunContext,
        category: str = "",
        search_term: str = "",
    ) -> str:
        """Look up Apple product prices. CALL THIS whenever the customer asks about a product by name, prices, or availability.
        Args:
            category: Filter by product type: iPhone, iPad, Mac, Accessories, Watch. Leave empty for all.
            search_term: Product name or keyword the customer said (e.g. 'iPhone 16', 'macbook', 'airpods').
        Returns:
            Product list. Present these to the customer in natural Bengali speech. Never read out order codes.
        """

        async def _speak_fetching_prices() -> None:
            await asyncio.sleep(TOOL_STATUS_UPDATE_DELAY)
            session = context.session
            await session.generate_reply(
                instructions="Reply with exactly one short Bengali sentence telling the customer to wait a moment while you check. Example: 'ektu darun, ami dekhchi.' Do not say anything else."
            )

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

        logger.info(
            "get_apple_prices (bn) called category=%r search_term=%r -> %d products from source",
            category_clean or "(all)",
            search_clean or "(none)",
            len(products),
        )
        if products:
            logger.info(
                "Sample product ids/names: %s",
                [(p.get("id"), p.get("name")) for p in products[:5]],
            )

        if category_clean:
            products = [p for p in products if (p.get("category") or "").lower() == category_clean]
        if search_clean:
            def _normalize_for_match(s: str) -> str:
                return (s or "").lower().replace(" ", "").replace("-", "")

            search_norm = _normalize_for_match(search_clean)
            products = [
                p
                for p in products
                if search_clean in (p.get("name") or "").lower()
                or search_clean in (p.get("id") or "").lower()
                or (search_norm and search_norm in _normalize_for_match(str(p.get("name") or "")))
                or (search_norm and search_norm in _normalize_for_match(str(p.get("id") or "")))
            ]

        logger.info("After filters (bn): %d products", len(products))

        if not products:
            return (
                "No matching products found. "
                "Tell the customer politely in Bengali that you could not find that product, "
                "and ask if they would like to look at a different category or try a different name."
            )

        lines = []
        for p in products:
            name = p.get("name", "Unknown")
            price = p.get("price_usd")
            desc = p.get("description", "")
            price_str = f"${price:,}" if price else "price unavailable"
            line = f"{name}: {price_str}"
            if desc:
                line += f" ({desc})"
            line += f" [order code: {p.get('id', '')}]"
            lines.append(line)

        return (
            f"{len(products)} product(s) found:\n"
            + "\n".join(lines)
            + "\n\nPresent these to the customer in natural Bengali speech. "
            "Say product names in English but describe prices and details in Bengali. "
            "Never read out the order codes aloud."
        )

    @function_tool()
    async def trigger_purchase(
        self,
        context: RunContext,
        product_id: str,
        quantity: int = 1,
        user_name: str = "",
    ) -> str:
        """Place a purchase order. Only call AFTER the customer confirmed they want to buy and gave their name.
        Args:
            product_id: The order code (e.g. iphone-16, airpods-pro-2).
            quantity: How many units (default 1).
            user_name: The customer's name (must ask before calling this).
        Returns:
            Result message. Relay to the customer in natural Bengali.
        """
        logger.info(
            "trigger_purchase (bn) CALLED — product_id=%s, quantity=%d, user_name=%s",
            product_id,
            quantity,
            user_name,
        )

        if not product_id or not product_id.strip():
            return (
                "Order could not be placed — no product specified. "
                "Ask the customer in Bengali which product they want to order."
            )

        if quantity < 1:
            return "Order could not be placed — quantity must be at least 1. Ask the customer again in Bengali."

        if not user_name or not user_name.strip():
            return (
                "Order could not be placed — customer name is required. "
                "Politely ask for their name in Bengali before placing the order."
            )

        product_name = next(
            (p["name"] for p in APPLE_PRODUCT_CATALOG if p.get("id") == product_id),
            None,
        )
        if product_name is None and N8N_PRICES_WEBHOOK_URL:
            try:
                webhook_products = await _fetch_prices_from_webhook()
                product_name = next(
                    (p.get("name") or product_id for p in webhook_products if (p.get("id") or "").lower() == product_id.strip().lower()),
                    product_id,
                )
            except Exception:
                product_name = product_id
        if product_name is None:
            product_name = product_id

        async def _speak_processing_order() -> None:
            await asyncio.sleep(TOOL_STATUS_UPDATE_DELAY)
            session = context.session
            await session.generate_reply(
                instructions="Reply with exactly one short Bengali sentence telling the customer their order is being processed. Example: 'apnar order process hochchhe, ektu opekkha korun.' Do not say anything else."
            )

        if N8N_PURCHASE_WEBHOOK_URL:
            status_task = asyncio.create_task(_speak_processing_order())
            try:
                result = await _trigger_n8n_purchase(product_id, product_name, quantity, user_name)
            finally:
                status_task.cancel()
                try:
                    await status_task
                except asyncio.CancelledError:
                    pass
        else:
            result = await _trigger_n8n_purchase(product_id, product_name, quantity, user_name)

        if result.get("success"):
            qty_label = f"{quantity}" if quantity > 1 else "1"
            return (
                f"Order successful! Customer {user_name.strip()} ordered {qty_label} x {product_name}. "
                f"Confirm this to the customer in a warm, friendly Bengali sentence. "
                f"Then say goodbye in Bengali and end the call."
            )
        error = result.get("error", "unknown issue")
        logger.error("Purchase failed (bn) for %s: %s", product_id, error)
        return (
            "The order failed due to a technical issue. "
            "Apologize to the customer in Bengali and ask them to try again shortly."
        )

    @function_tool()
    async def end_call(
        self,
        context: RunContext,
        reason: str = "conversation complete",
    ) -> str:
        """End the phone call and disconnect. Call this AFTER you have already said goodbye in Bengali.
        Args:
            reason: Brief reason (e.g. 'purchase complete', 'customer not interested').
        """
        logger.info("Bengali agent ending call — reason: %s", reason)

        async def _delayed_disconnect() -> None:
            await asyncio.sleep(self.END_CALL_DELAY)
            self._disconnect_event.set()

        asyncio.create_task(_delayed_disconnect())
        return "Call is ending now. Do not say anything else."


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext) -> None:
    room_name = ctx.room.name
    logger.info("Apple seller Bengali agent connecting to room: %s", room_name)

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    logger.info("Apple seller Bengali agent connected to room: %s", room_name)

    disconnect_event = asyncio.Event()

    session = AgentSession(
        # --- STT: Google Cloud Speech-to-Text (Bengali) ---
        stt=google.STT(
            languages="bn-BD",
            model="chirp_2",
            location="asia-southeast1",
        ),

        # --- LLM: Gemini 2.5 Flash ---
        llm=google.LLM(model="gemini-2.5-flash", temperature=0.7),

        # --- TTS: Gemini TTS (multilingual, supports Bengali) ---
        # Voices: Kore, Puck, Charon, Fenrir, Aoede, Leda, Orus, Zephyr
        tts=google.TTS(
            model_name="gemini-2.5-flash-tts",
            voice_name="Kore",
            language="bn-BD",
            prompt="Speak in a warm, friendly, natural Bengali tone. Moderate pace, clear pronunciation.",
            speaking_rate=1.15,
        ),

        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        agent=AppleSellerAgentBn(disconnect_event=disconnect_event),
        room=ctx.room,
    )

    logger.info("Apple seller Bengali session started in room: %s", room_name)
    await session.say("আসসালামু আলাইকুম! আমি আপনার Apple বিক্রয় সহকারী। আপনি কী খুঁজছেন?")
    logger.info("Bengali greeting sent, session running...")

    async def on_shutdown() -> None:
        disconnect_event.set()

    ctx.add_shutdown_callback(on_shutdown)
    await disconnect_event.wait()
    logger.info("Apple seller Bengali agent leaving room: %s", room_name)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="apple-seller-agent-bn",
        ),
    )
