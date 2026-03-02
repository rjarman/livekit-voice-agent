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

    # Delay after goodbye before actually disconnecting, so TTS finishes speaking
    END_CALL_DELAY = 2.0

    def __init__(self, disconnect_event: asyncio.Event) -> None:
        self._disconnect_event = disconnect_event
        super().__init__(
            instructions="""\
You are a friendly Apple product seller in a voice call. The user is talking to you via voice.
Your job is to help them find the right Apple product (iPhone, iPad, Mac, AirPods, Apple Watch, etc.) and complete a purchase if they want.

ABSOLUTE RULES — FOLLOW EVERY SINGLE ONE:
1. You MUST speak ONLY natural, conversational sentences. You are talking to a real person on a phone call.
2. NEVER say any word that looks like a function name, variable name, parameter name, or code. Examples of FORBIDDEN words: "get_apple_prices", "trigger_purchase", "product_id", "price_usd", "search_term", "category", "user_name", "quantity". If you catch yourself about to say any underscore-containing word or any technical term, STOP and rephrase as a normal human sentence.
3. NEVER narrate or describe what you are doing internally. Do NOT say things like "Let me call...", "I'm going to use...", "Fetching with category...", "Looking up with search term...", or "I'll trigger the...". Just DO it silently, then speak the result naturally.
4. NEVER read out JSON keys, field names, or argument values. When you receive product data, translate it to natural speech: say "seven ninety-nine dollars" not "price_usd 799", say "the iPhone 16" not "product_id iphone-16".
5. Keep your replies short and voice-friendly. List at most 3-4 products at a time. If there are more, offer to tell them about the rest.
6. When the user wants to buy, ask for their name first if you don't have it, confirm the product and quantity, then place the order and tell them the result.
7. If the user is unsure, suggest 2-3 options based on their needs. Do not make up prices — always use the tools to get real data.
8. Do not use emojis, asterisks, bullet points, or any visual formatting. Speak in plain sentences.
9. ENDING THE CALL: After a successful purchase, say a brief thank-you and goodbye, then end the call. If the customer says they are not interested, not looking to buy, or wants to end the conversation, say a polite goodbye and end the call. Always say goodbye BEFORE ending the call so the customer hears it."""
        )

    @function_tool()
    async def get_apple_prices(
        self,
        context: RunContext,
        category: str = "",
        search_term: str = "",
    ) -> str:
        """Look up Apple product prices. Use when the customer asks about prices, products, or what is available.
        Args:
            category: Filter by product type: iPhone, iPad, Mac, Accessories, Watch. Leave empty to show all.
            search_term: Optional keyword to narrow results (e.g. 'pro', 'air', 'macbook').
        Returns:
            A plain-English summary of matching products. Read it back to the customer naturally — never read out field names or IDs.
        """
        async def _speak_fetching_prices() -> None:
            await asyncio.sleep(TOOL_STATUS_UPDATE_DELAY)
            await context.session.generate_reply(
                instructions="Say one very short sentence: you are checking the latest prices, one moment. No lists or details."
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

        if category_clean:
            products = [p for p in products if (p.get("category") or "").lower() == category_clean]
        if search_clean:
            products = [
                p for p in products
                if search_clean in (p.get("name") or "").lower() or search_clean in (p.get("id") or "").lower()
            ]

        if not products:
            return "No matching products found. Ask the customer if they'd like to try a different category or search."

        # Build a human-readable summary so the LLM doesn't read out raw field names
        lines = []
        for p in products:
            name = p.get("name", "Unknown")
            price = p.get("price_usd")
            desc = p.get("description", "")
            price_str = f"${price:,}" if price else "price unavailable"
            line = f"{name}: {price_str}"
            if desc:
                line += f" ({desc})"
            # Attach the internal ID so the LLM can call the purchase tool, but label it clearly
            line += f" [order code: {p.get('id', '')}]"
            lines.append(line)

        return (
            f"{len(products)} product(s) available:\n"
            + "\n".join(lines)
            + "\n\nTell the customer about these products in natural speech. Never read out the order codes — those are only for placing orders internally."
        )

    @function_tool()
    async def trigger_purchase(
        self,
        context: RunContext,
        product_id: str,
        quantity: int = 1,
        user_name: str = "",
    ) -> str:
        """Place a purchase order for the customer. Only call this AFTER the customer has confirmed they want to buy and has provided their name.
        Args:
            product_id: The order code for the product (e.g. iphone-16, airpods-pro-2).
            quantity: How many units to order (default 1).
            user_name: The customer's name (you must ask for it before calling this).
        Returns:
            A plain-English result. Relay it to the customer naturally — never read out technical details.
        """
        # Validate inputs
        if not product_id or not product_id.strip():
            return "Could not place the order — no product was specified. Ask the customer which product they want."

        if quantity < 1:
            return "Could not place the order — the quantity must be at least 1."

        if not user_name or not user_name.strip():
            return "Could not place the order — the customer's name is required. Please ask for their name first."

        product_name = next(
            (p["name"] for p in APPLE_PRODUCT_CATALOG if p.get("id") == product_id),
            product_id,
        )

        async def _speak_processing_order() -> None:
            await asyncio.sleep(TOOL_STATUS_UPDATE_DELAY)
            await context.session.generate_reply(
                instructions="Say one very short sentence: processing your order, one moment. No lists or details."
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

        # Convert the raw result to a human-readable message
        if result.get("success"):
            qty_str = f"{quantity} unit(s) of" if quantity > 1 else ""
            return (
                f"Order placed successfully! {user_name.strip()} ordered {qty_str} {product_name}. "
                f"Confirm this to the customer in a friendly way."
            )
        else:
            error = result.get("error", "unknown issue")
            logger.error("Purchase failed for %s: %s", product_id, error)
            return "Sorry, something went wrong while placing the order. Ask the customer to try again in a moment."

    @function_tool()
    async def end_call(
        self,
        context: RunContext,
    ) -> str:
        """End the phone call and disconnect. Call this AFTER you have already said goodbye to the customer.
        Use this when:
        - The customer has completed a purchase and you have confirmed the order and said thank you.
        - The customer says they are not interested, do not want to buy, or want to hang up.
        Always say a friendly goodbye sentence BEFORE calling this.
        """
        logger.info("Agent ending call — goodbye spoken, disconnecting.")

        async def _delayed_disconnect() -> None:
            # Wait briefly so the TTS goodbye finishes playing before we disconnect
            await asyncio.sleep(self.END_CALL_DELAY)
            self._disconnect_event.set()

        asyncio.create_task(_delayed_disconnect())
        return "Call is ending. Do not say anything else."


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext) -> None:
    room_name = ctx.room.name
    logger.info("Apple seller agent connecting to room: %s", room_name)

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    logger.info("Apple seller agent connected to room: %s", room_name)

    disconnect_event = asyncio.Event()

    session = AgentSession(
        stt=assemblyai.STT(),
        llm=groq.LLM(model="llama-3.1-8b-instant"),
        tts=cartesia.TTS(),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        agent=AppleSellerAgent(disconnect_event=disconnect_event),
        room=ctx.room,
    )

    logger.info("Apple seller session started in room: %s", room_name)
    await session.say("Hi! I'm your Apple sales assistant. I can show you our latest products and prices, or help you place an order. What are you looking for?")
    logger.info("Greeting sent, session running...")

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
