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
from livekit.plugins import cartesia, google, groq, openai, silero

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
        super().__init__(
            instructions="""\
আপনি একটি ভয়েস কলে একজন বন্ধুত্বপূর্ণ Apple পণ্যের বিক্রেতা। ব্যবহারকারী আপনার সাথে বাংলায় কথা বলছে।
আপনার কাজ হলো গ্রাহককে সঠিক Apple পণ্য (iPhone, iPad, Mac, AirPods, Apple Watch ইত্যাদি) বেছে নিতে সাহায্য করা এবং তারা চাইলে ক্রয় সম্পন্ন করা।

কঠোর নিয়ম — প্রতিটা অবশ্যই মেনে চলবেন:
1. আপনি সবসময় শুধু স্বাভাবিক, কথোপকথনের মতো বাংলা বাক্যে কথা বলবেন। ছোট, পরিষ্কার বাক্য ব্যবহার করবেন।
2. কখনও কোনো ফাংশনের নাম, ভেরিয়েবলের নাম, প্যারামিটারের নাম, বা কোডের মতো শব্দ উচ্চারণ করবেন না। উদাহরণ: "get_apple_prices", "trigger_purchase", "product_id", "price_usd", "search_term", "category", "user_name", "quantity" — এ ধরনের কোনো শব্দ মুখে আনবেন না। যদি মনে হয় এমন কিছু বলছেন, সাথে সাথেই সাধারণ বাংলায় বলে নেবেন।
3. আপনি ভেতরে কী করছেন তা কখনও মুখে বলবেন না। যেমন: "আমি এখন দামের তথ্য আনছি", "আমি একটা টুল কল করছি", "আমি এখন সার্চ করছি" — এসব কথা বলবেন না। ভেতরের কাজ চুপচাপ করবেন, বাইরে শুধু ফলাফলের উপর ভিত্তি করে স্বাভাবিকভাবে কথা বলবেন।
4. কখনও JSON কী, ফিল্ডের নাম, বা আর্গুমেন্টের মান পড়ে শোনাবেন না। সবসময় ডেটাকে প্রাকৃতিক কথায় রূপান্তর করবেন। যেমন "price_usd 799" না বলে বলবেন "দাম প্রায় সাতশো নিরানব্বই ডলার", আর "product_id iphone-16" না বলে বলবেন "iPhone 16"।
5. প্রতিবার উত্তরে কণ্ঠস্বরের জন্য উপযোগী, ছোট ও সহজ উত্তর দিন। একবারে সর্বোচ্চ তিন থেকে চারটি পণ্যের কথা বলবেন। এর বেশি থাকলে গ্রাহককে জিজ্ঞেস করুন, আরও শুনতে চান কি না।
6. গ্রাহক যখন কিনতে চাইবেন, আগে যদি নাম না জানা থাকে, বিনয়ের সাথে তার নাম জিজ্ঞেস করুন, তারপর যে পণ্য আর যত পরিমাণ কিনতে চান তা আবার একবার নিশ্চিত করুন, তারপর অর্ডার দিন এবং ফলাফল পরিষ্কার বাংলায় জানিয়ে দিন।
7. যদি গ্রাহক দ্বিধায় থাকেন, তাদের প্রয়োজন বুঝে দুই–তিনটি অপশন সাজেস্ট করুন। কখনও দাম আন্দাজ করে বলবেন না — সবসময় দামের তথ্য পেতে নির্ধারিত টুল ব্যবহার করবেন।
8. গ্রাহক যখন কোনো নির্দিষ্ট পণ্যের নাম বা ধরন (যেমন iPhone 17, iPhone 16, MacBook, iPad) নিয়ে দাম বা প্রাপ্যতা জানতে চাইবেন, তখন আপনাকে অবশ্যই প্রথমে প্রাইস লুকআপ টুল কল করতে হবে। টুল না ডেকে কখনও বলবেন না যে কোনো পণ্য নেই বা স্টকে নেই — আমাদের ক্যাটালগে অতিরিক্ত পণ্য থাকতে পারে।
9. কোনো ইমোজি, তারকা চিহ্ন, বুলেট পয়েন্ট বা অন্য কোনো ভিজ্যুয়াল ফরম্যাটিং ব্যবহার করবেন না। শুধুই সাধারণ বাংলা বাক্য ব্যবহার করবেন।
10. কল শেষ করার নিয়ম: অর্ডার সফল হলে এক লাইনের মত করে ধন্যবাদ ও বিদায় জানিয়ে তারপর কল শেষ করবেন। যদি গ্রাহক বলে যে তারা আগ্রহী না, কিনতে চায় না, বা কথা শেষ করতে চায়, তাহলে ভদ্রভাবে বাংলায় ধন্যবাদ ও বিদায় জানিয়ে কল শেষ করবেন। সবসময় কল কেটে দেওয়ার আগে বিদায় বাক্যটি বলবেন যাতে গ্রাহক সেটা শুনতে পারেন।"""
        )

    @function_tool()
    async def get_apple_prices(
        self,
        context: RunContext,
        category: str = "",
        search_term: str = "",
    ) -> str:
        """Look up Apple product prices. Same semantics as the English agent."""

        async def _speak_fetching_prices() -> None:
            await asyncio.sleep(TOOL_STATUS_UPDATE_DELAY)
            await context.session.generate_reply(
                instructions="Say one very short sentence in Bengali: you are checking the latest prices, one moment. No lists or details."
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
            "get_apple_prices (bn) called category=%r search_term=%r → %d products from source",
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
            # Match flexibly: "iphone 17" should match id "iphone-17" and name "iPhone 17"
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
            return "কোনো মিল পাওয়া যায়নি। গ্রাহককে বিনয়ের সাথে জিজ্ঞেস করুন, তারা কি অন্য ক্যাটাগরি বা ভিন্নভাবে খুঁজতে চান।"

        # Keep the same English text structure so tools stay interoperable; the agent will still speak Bengali.
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
            f"{len(products)} product(s) available:\n"
            + "\n".join(lines)
            + "\n\nTell the customer about these products in natural Bengali speech. Never read out the order codes — those are only for placing orders internally."
        )

    @function_tool()
    async def trigger_purchase(
        self,
        context: RunContext,
        product_id: str,
        quantity: int = 1,
        user_name: str = "",
    ) -> str:
        """Place a purchase order for the customer. Same behavior as English agent."""
        logger.info(
            "trigger_purchase (bn) CALLED — product_id=%s, quantity=%d, user_name=%s",
            product_id,
            quantity,
            user_name,
        )

        if not product_id or not product_id.strip():
            return "অর্ডার করা সম্ভব হয়নি — কোনো পণ্যের তথ্য পাওয়া যায়নি। আগে গ্রাহকের কাছ থেকে নিশ্চিত হয়ে পণ্যের নাম জেনে নিন।"

        if quantity < 1:
            return "অর্ডার করা সম্ভব হয়নি — পরিমাণ কমপক্ষে ১ হতে হবে।"

        if not user_name or not user_name.strip():
            return "অর্ডার করা সম্ভব হয়নি — গ্রাহকের নাম প্রয়োজন। আগে বিনয়ের সাথে নাম জেনে নিন।"

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
            await context.session.generate_reply(
                instructions="Say one very short sentence in Bengali: you are processing the order, one moment. No lists or details."
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
            qty_str = f"{quantity} টি" if quantity > 1 else "১ টি"
            return (
                f"অর্ডার সফল হয়েছে! {user_name.strip()} {qty_str} {product_name} অর্ডার করেছেন। "
                f"গ্রাহককে বন্ধুত্বপূর্ণভাবে বাংলায় এটি নিশ্চিত করে বলুন।"
            )
        error = result.get("error", "unknown issue")
        logger.error("Purchase failed (bn) for %s: %s", product_id, error)
        return "দুঃখিত, অর্ডার করার সময় একটি সমস্যা হয়েছে। গ্রাহককে অনুরোধ করুন একটু পরে আবার চেষ্টা করতে।"

    @function_tool()
    async def end_call(
        self,
        context: RunContext,
        reason: str = "conversation complete",
    ) -> str:
        """End the phone call and disconnect. Same semantics, but caller speaks Bengali."""
        logger.info("Bengali agent ending call — reason: %s", reason)

        async def _delayed_disconnect() -> None:
            await asyncio.sleep(self.END_CALL_DELAY)
            self._disconnect_event.set()

        asyncio.create_task(_delayed_disconnect())
        return "কল এখন শেষ হচ্ছে। আর কিছু বলবেন না।"


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext) -> None:
    room_name = ctx.room.name
    logger.info("Apple seller Bengali agent connecting to room: %s", room_name)

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    logger.info("Apple seller Bengali agent connected to room: %s", room_name)

    disconnect_event = asyncio.Event()

    session = AgentSession(
        stt=cartesia.STT(),
        # llm=groq.LLM(model="llama-3.3-70b-versatile"),
        llm=openai.LLM.with_azure(
            model="gpt-4o-mini",
            azure_deployment="gpt-4o-mini",
            azure_endpoint=os.environ["AZURE_LLM_ENDPOINT"],
            api_key=os.environ["AZURE_LLM_API_KEY"],
            api_version="2025-01-01-preview",
        ),
        # llm=google.LLM(model="google/gemini-2.5-flash-lite"),
        tts=cartesia.TTS(),
        # If you prefer Azure instead of Groq/Cartesia, you can switch these the same way as in the English agent.
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        agent=AppleSellerAgentBn(disconnect_event=disconnect_event),
        room=ctx.room,
    )

    logger.info("Apple seller Bengali session started in room: %s", room_name)
    await session.say("হ্যালো! আমি আপনার Apple বিক্রয় সহকারী। আমি আপনাকে আমাদের সর্বশেষ পণ্য আর তাদের দাম জানাতে পারি, অথবা আপনার হয়ে অর্ডার করতে পারি। আপনি কী খুঁজছেন?")
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

