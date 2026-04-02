"""
Blocks Cloud Support Voice Agent for LiveKit.

RAG-enabled voice agent that answers questions about Blocks Cloud documentation.
Uses OpenAI RealtimeModel for low-latency voice + Qdrant for vector search.
"""

import asyncio
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

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
from livekit.plugins import openai, silero

load_dotenv()

logger = logging.getLogger("blocks-support-agent")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = "blocks-cloud-docs"
EMBEDDING_MODEL = "text-embedding-3-small"
DOCS_DIR = os.getenv("DOCS_DIR", "/app/docs/cloud")
TOP_K = 3

# ---------------------------------------------------------------------------
# Chunking: split markdown by ## headings
# ---------------------------------------------------------------------------

def _chunk_markdown(text: str, file_path: str) -> list[dict[str, str]]:
    """Split markdown into chunks by ## headings. Files < 100 lines kept whole."""
    # Strip frontmatter
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
    text = text.strip()
    if not text:
        return []

    lines = text.split("\n")
    rel_path = file_path.split("docs/cloud/")[-1] if "docs/cloud/" in file_path else file_path

    # Small files: keep whole
    if len(lines) < 100:
        return [{"text": text, "source": rel_path, "heading": ""}]

    chunks: list[dict[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []

    for line in lines:
        if re.match(r"^#{1,2}\s+", line):
            # Save previous chunk
            if current_lines:
                chunk_text = "\n".join(current_lines).strip()
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "source": rel_path,
                        "heading": current_heading,
                    })
            current_heading = line.lstrip("#").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    # Last chunk
    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "source": rel_path,
                "heading": current_heading,
            })

    return chunks


def _load_all_chunks(docs_dir: str) -> list[dict[str, str]]:
    """Load and chunk all .md files from the docs directory."""
    all_chunks: list[dict[str, str]] = []
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        logger.warning("Docs directory not found: %s", docs_dir)
        return []

    for md_file in sorted(docs_path.rglob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
            chunks = _chunk_markdown(text, str(md_file))
            all_chunks.extend(chunks)
        except Exception as e:
            logger.warning("Failed to read %s: %s", md_file, e)

    logger.info("Loaded %d chunks from %s", len(all_chunks), docs_dir)
    return all_chunks


# ---------------------------------------------------------------------------
# Qdrant indexing: embed + store on startup (skip if collection exists)
# ---------------------------------------------------------------------------

async def _ensure_qdrant_indexed() -> None:
    """Check if Qdrant collection exists; if not, chunk+embed+store all docs."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    import openai as oai

    t0 = time.monotonic()
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)

    # Check if collection already exists
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in collections:
        count = client.get_collection(COLLECTION_NAME).points_count
        logger.info(
            "[TIMING] Qdrant collection '%s' already exists (%d points) — skipping indexing (%.2fs)",
            COLLECTION_NAME, count, time.monotonic() - t0,
        )
        client.close()
        return

    # Load and chunk docs
    chunks = _load_all_chunks(DOCS_DIR)
    if not chunks:
        logger.warning("No chunks to index — docs directory may be empty")
        client.close()
        return

    # Embed all chunks
    t_embed = time.monotonic()
    oai_client = oai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    texts = [c["text"] for c in chunks]

    # Batch embeddings (API allows up to 2048 inputs)
    response = oai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    embeddings = [item.embedding for item in response.data]
    dim = len(embeddings[0])
    logger.info(
        "[TIMING] Embedded %d chunks (dim=%d) in %.2fs",
        len(chunks), dim, time.monotonic() - t_embed,
    )

    # Create collection and upsert
    t_store = time.monotonic()
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    points = [
        PointStruct(
            id=i,
            vector=embeddings[i],
            payload={
                "text": chunks[i]["text"],
                "source": chunks[i]["source"],
                "heading": chunks[i]["heading"],
            },
        )
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info(
        "[TIMING] Stored %d points in Qdrant in %.2fs (total indexing: %.2fs)",
        len(points), time.monotonic() - t_store, time.monotonic() - t0,
    )
    client.close()


async def _search_qdrant(query: str, top_k: int = TOP_K) -> list[dict[str, Any]]:
    """Search Qdrant for relevant doc chunks."""
    from qdrant_client import QdrantClient
    import openai as oai

    oai_client = oai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = oai_client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
    query_vector = response.data[0].embedding

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
    )
    client.close()

    return [
        {
            "text": hit.payload["text"],
            "source": hit.payload.get("source", ""),
            "heading": hit.payload.get("heading", ""),
            "score": hit.score,
        }
        for hit in results
    ]


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class BlocksSupportAgent(Agent):
    """Voice agent that answers Blocks Cloud questions using RAG."""

    END_CALL_DELAY = 2.0

    def __init__(self, disconnect_event: asyncio.Event) -> None:
        self._disconnect_event = disconnect_event
        super().__init__(
            instructions="""\
You are a Blocks Cloud support agent on a voice call.

LANGUAGE RULES — CRITICAL:
1. Your greeting is ALWAYS bilingual: Bengali first, then English.
2. In the greeting, ask the customer which language they prefer: Bengali or English.
3. Once the customer picks a language (by replying in Bengali or English, or by explicitly choosing), \
you MUST use ONLY that language for the ENTIRE rest of the conversation. NEVER switch languages mid-conversation.
4. If the customer picked Bengali, speak ONLY in natural Bengali (except technical terms like "Blocks Cloud", "deploy", "API").
5. If the customer picked English, speak ONLY in English.

BEHAVIOR RULES:
1. You are a helpful support agent for Blocks Cloud — a developer-focused cloud platform.
2. When the customer asks a question, you MUST call the search_docs tool first to find relevant documentation. \
Never answer from memory — always search first.
3. Keep answers short and conversational — this is a voice call, not a chat. Maximum 2-3 sentences per reply.
4. If the search returns no relevant results, say you don't have information on that topic and suggest \
they check the Blocks Cloud documentation at docs.seliseblocks.com.
5. NEVER read out URLs, file paths, code blocks, or markdown formatting. Describe things in plain spoken language.
6. No emoji, no asterisks, no bullet points. Plain spoken sentences only.
7. NEVER spell out numbers as digits. Always say them as words.
8. After helping, ask if they have more questions. If they say no or want to end, say goodbye and end the call."""
        )

    @function_tool()
    async def search_docs(
        self,
        context: RunContext,
        query: str,
    ) -> str:
        """Search Blocks Cloud documentation for information. ALWAYS call this when the customer asks any question about Blocks Cloud features, setup, deployment, or usage.
        Args:
            query: The customer's question or topic to search for (e.g. 'how to deploy', 'authentication setup', 'what is data connect').
        Returns:
            Relevant documentation excerpts. Present the information to the customer in their chosen language.
        """
        t0 = time.monotonic()
        logger.info("[TIMING] search_docs START — query=%r", query)

        try:
            results = await _search_qdrant(query, top_k=TOP_K)
        except Exception as e:
            logger.error("Qdrant search failed: %s", e)
            return "Documentation search is currently unavailable. Apologize and suggest they visit docs.seliseblocks.com."

        logger.info(
            "[TIMING] search_docs END — %.2fs, %d results",
            time.monotonic() - t0, len(results),
        )

        if not results or results[0]["score"] < 0.3:
            return (
                "No relevant documentation found for this query. "
                "Tell the customer you don't have specific information on this topic, "
                "and suggest they check docs.seliseblocks.com for more details."
            )

        # Build context from top results
        context_parts = []
        for r in results:
            source = r["source"]
            heading = r["heading"]
            label = f"[{source}"
            if heading:
                label += f" > {heading}"
            label += "]"
            context_parts.append(f"{label}\n{r['text']}")

        return (
            "Documentation found:\n\n"
            + "\n\n---\n\n".join(context_parts)
            + "\n\nAnswer the customer's question based on this documentation. "
            "Keep it to 2-3 short spoken sentences. "
            "Do NOT read out file paths, URLs, or markdown formatting. "
            "Speak naturally in the customer's chosen language."
        )

    @function_tool()
    async def end_call(
        self,
        context: RunContext,
        reason: str = "conversation complete",
    ) -> str:
        """End the phone call and disconnect. Call this AFTER you have said goodbye.
        Args:
            reason: Brief reason (e.g. 'support complete', 'customer done').
        """
        logger.info("[TIMING] end_call — reason: %s", reason)

        async def _delayed_disconnect() -> None:
            await asyncio.sleep(self.END_CALL_DELAY)
            self._disconnect_event.set()

        asyncio.create_task(_delayed_disconnect())
        return "Call is ending now. Do not say anything else."


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext) -> None:
    room_name = ctx.room.name
    t_start = time.monotonic()
    logger.info("[TIMING] entrypoint START — room: %s", room_name)

    # Index docs into Qdrant (skips if already done)
    await _ensure_qdrant_indexed()
    logger.info("[TIMING] Qdrant indexing check — %.2fs", time.monotonic() - t_start)

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    logger.info("[TIMING] connected to room — %.2fs", time.monotonic() - t_start)

    disconnect_event = asyncio.Event()

    t_model = time.monotonic()
    realtime_model = openai.realtime.RealtimeModel(
        model="gpt-realtime-1.5",
        voice="coral",
        temperature=0.7,
    )
    logger.info("[TIMING] RealtimeModel created — %.2fs", time.monotonic() - t_model)

    session = AgentSession(
        llm=realtime_model,
        vad=ctx.proc.userdata["vad"],
    )

    t_session = time.monotonic()
    await session.start(
        agent=BlocksSupportAgent(disconnect_event=disconnect_event),
        room=ctx.room,
    )
    logger.info("[TIMING] session.start() — %.2fs", time.monotonic() - t_session)

    t_greet = time.monotonic()
    await session.generate_reply(
        instructions=(
            "Greet the customer in Bengali first, then English. "
            "Introduce yourself as a Blocks Cloud support assistant. "
            "Ask which language they prefer: Bengali or English. "
            "Keep it short — 3 sentences max. "
            "Example: 'Assalamu Alaikum! Ami Blocks Cloud er support assistant. "
            "Apni ki Banglay shahajjo chan naki English e?' "
            "Then in English: 'Welcome! I am your Blocks Cloud support assistant. "
            "Would you prefer Bengali or English?'"
        )
    )
    logger.info(
        "[TIMING] greeting generate_reply — %.2fs (total from start: %.2fs)",
        time.monotonic() - t_greet, time.monotonic() - t_start,
    )

    async def on_shutdown() -> None:
        disconnect_event.set()

    ctx.add_shutdown_callback(on_shutdown)
    await disconnect_event.wait()
    logger.info("Blocks support agent leaving room: %s", room_name)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="blocks-support-agent",
        ),
    )
