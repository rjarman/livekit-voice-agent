"""
Blocks Cloud Support Voice Agent for LiveKit.

RAG-enabled voice agent that answers questions about Blocks Cloud documentation.
Uses Qwen via DashScope (STT+LLM+TTS pipeline) for voice + Qdrant for vector search.
Falls back to OpenAI Realtime if DASHSCOPE_API_KEY is not set.
Supports human handoff via SIP call — agent goes deaf+mute during human conversation,
records and transcribes in real-time, resumes with full context when human hangs up.
"""

import asyncio
import io
import logging
import os
import re
import struct
import time
import wave
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from livekit import api as lkapi, rtc
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
from livekit.plugins.qwen import RealtimeModel as QwenRealtimeModel

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

# Human handoff config
SUPPORT_PHONE_NUMBER = os.getenv("SUPPORT_PHONE_NUMBER", "")
SUPPORT_SIP_TRUNK_ID = os.getenv("SUPPORT_SIP_TRUNK_ID", "")
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://livekit:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

HUMAN_SUPPORT_IDENTITY_PREFIX = "support-human-"
# Transcribe audio in chunks of this many seconds during handoff
TRANSCRIBE_CHUNK_SECONDS = 10
SAMPLE_RATE = 48000
NUM_CHANNELS = 1


# ---------------------------------------------------------------------------
# Chunking: split markdown by ## headings
# ---------------------------------------------------------------------------

def _chunk_markdown(text: str, file_path: str) -> list[dict[str, str]]:
    """Split markdown into chunks by ## headings. Files < 100 lines kept whole."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
    text = text.strip()
    if not text:
        return []

    lines = text.split("\n")
    rel_path = file_path.split("docs/cloud/")[-1] if "docs/cloud/" in file_path else file_path

    if len(lines) < 100:
        return [{"text": text, "source": rel_path, "heading": ""}]

    chunks: list[dict[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []

    for line in lines:
        if re.match(r"^#{1,2}\s+", line):
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
# Qdrant indexing
# ---------------------------------------------------------------------------

async def _ensure_qdrant_indexed() -> None:
    """Check if Qdrant collection exists; if not, chunk+embed+store all docs."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    import openai as oai

    t0 = time.monotonic()
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)

    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in collections:
        count = client.get_collection(COLLECTION_NAME).points_count
        logger.info(
            "[TIMING] Qdrant collection '%s' already exists (%d points) — skipping indexing (%.2fs)",
            COLLECTION_NAME, count, time.monotonic() - t0,
        )
        client.close()
        return

    chunks = _load_all_chunks(DOCS_DIR)
    if not chunks:
        logger.warning("No chunks to index — docs directory may be empty")
        client.close()
        return

    t_embed = time.monotonic()
    oai_client = oai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    texts = [c["text"] for c in chunks]

    response = oai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    embeddings = [item.embedding for item in response.data]
    dim = len(embeddings[0])
    logger.info(
        "[TIMING] Embedded %d chunks (dim=%d) in %.2fs",
        len(chunks), dim, time.monotonic() - t_embed,
    )

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
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
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
        for hit in results.points
    ]


# ---------------------------------------------------------------------------
# Audio recording + transcription helpers
# ---------------------------------------------------------------------------

def _audio_frames_to_wav_bytes(frames: list[bytes], sample_rate: int, num_channels: int) -> bytes:
    """Convert raw PCM int16 frames to WAV bytes for Whisper."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(2)  # int16 = 2 bytes
        wf.setframerate(sample_rate)
        for frame in frames:
            wf.writeframes(frame)
    return buf.getvalue()


async def _transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe WAV audio using OpenAI Whisper."""
    import openai as oai

    oai_client = oai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "handoff_audio.wav"

    try:
        transcript = oai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=None,  # auto-detect Bengali/English
        )
        return transcript.text
    except Exception as e:
        logger.error("[HANDOFF] Whisper transcription failed: %s", e)
        return ""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class BlocksSupportAgent(Agent):
    """Voice agent that answers Blocks Cloud questions using RAG and human handoff."""

    END_CALL_DELAY = 2.0

    def __init__(self, disconnect_event: asyncio.Event, room: Any) -> None:
        self._disconnect_event = disconnect_event
        self._room = room
        self._handoff_active = False
        self._last_topic = ""
        self._language = "en"  # default; set by set_language tool
        super().__init__(
            instructions="""\
You are a Blocks Cloud support agent on a voice call.

GREETING RULE — ABSOLUTE:
You MUST greet with "Assalamu Alaikum" ONLY ONCE at the very start of the conversation. \
NEVER say "Namaskar", "Nomoshkar", or "Namaste". \
After the first greeting, NEVER repeat it. Just respond to the user's question directly.

LANGUAGE AND ACCENT:
The user speaks Bengali (Bangla) or English. You MUST speak in Bengali or English — NEVER in Chinese or any other language. \
Your speech should sound natural, not Chinese-accented. The user is from Bangladesh.

LANGUAGE RULES:
1. Your greeting is ALWAYS bilingual: Bengali first, then English.
2. In the greeting, ask the customer which language they prefer: Bengali or English.
3. As soon as the customer picks a language, you MUST call the set_language tool with 'bn' or 'en'. \
This is MANDATORY — always call set_language before responding in their chosen language.
4. Once set, use ONLY that language for the ENTIRE rest of the conversation. \
NEVER switch languages mid-conversation, even if the customer mixes languages occasionally.
5. If Bengali: speak natural Bengali (except product names like "Blocks Cloud", "deploy", "API").
6. If English: speak ONLY in English.

BEHAVIOR RULES:
1. You are a helpful support agent for Blocks Cloud — a developer-focused cloud platform.
2. When the customer asks a question, you MUST call the search_docs tool first. Never answer from memory.
3. Keep answers short — maximum 2-3 sentences. This is a voice call.
4. If search returns no results, offer to transfer to a human support agent.
5. NEVER read out URLs, file paths, code blocks, or markdown. Describe in plain spoken language.
6. No emoji, asterisks, bullet points. Plain spoken sentences only.
7. NEVER spell out numbers as digits. Say them as words.
8. After helping, ask if they have more questions. If done, say goodbye and end the call.

HUMAN HANDOFF RULES:
1. If the customer asks for a human, or you cannot answer after searching, offer to transfer.
2. If they confirm, call transfer_to_human with a brief summary in the customer's language.
3. After calling transfer_to_human, tell the customer to wait. Then stay quiet. \
The system will handle the summary and resume automatically — do NOT speak during the handoff.

EXAMPLES — follow these patterns exactly:

Example 1 — Greeting:
You: "Assalamu Alaikum! Ami Blocks Cloud er support assistant. Apni ki Banglay shahajjo chan naki English e? \
Welcome! I am your Blocks Cloud support assistant. Would you prefer Bengali or English?"

Example 2 — Customer picks Bengali:
Customer: "Bangla"
You: [calls set_language with 'bn']
You: [calls search_docs if they asked a question, or responds in Bengali]

Example 3 — Handoff:
Customer: "Ami ekjon manush er shathe kotha bolte chai"
You: "Jee, ami apnake ekjon support agent er shathe connect korchhi. Ektu opekkha korun."
[calls transfer_to_human with summary in Bengali]
[system handles the rest — agent stays quiet until system resumes it]
"""
        )

    @function_tool()
    async def set_language(
        self,
        context: RunContext,
        language: str,
    ) -> str:
        """Set the customer's preferred language. You MUST call this as soon as the customer chooses Bengali or English.
        Args:
            language: 'bn' for Bengali or 'en' for English.
        """
        self._language = language if language in ("bn", "en") else "en"
        logger.info("[LANG] Customer language set to: %s", self._language)
        return f"Language set to {'Bengali' if self._language == 'bn' else 'English'}. Continue in this language."

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
        self._last_topic = query

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
                "Tell the customer you don't have specific information on this topic. "
                "Ask if they would like to be transferred to a human support agent who can help further."
            )

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
    async def transfer_to_human(
        self,
        context: RunContext,
        issue_summary: str = "",
    ) -> str:
        """Transfer the customer to a human support agent via phone call. Call this when:
        - The customer explicitly asks to speak with a human or real person.
        - You cannot find relevant documentation to answer their question.
        - The customer is frustrated or needs specialized help.
        Args:
            issue_summary: A brief 1-sentence summary of what the customer needs help with.
        """
        if not SUPPORT_PHONE_NUMBER or not SUPPORT_SIP_TRUNK_ID:
            logger.warning("Human handoff not configured — SUPPORT_PHONE_NUMBER or SUPPORT_SIP_TRUNK_ID missing")
            return (
                "Human support transfer is not available right now. "
                "Apologize and suggest the customer contact support at support@seliseblocks.com "
                "or visit docs.seliseblocks.com for help."
            )

        if self._handoff_active:
            return "A human agent is already being connected. Please wait."

        summary = issue_summary or self._last_topic or "general support inquiry"
        logger.info("[HANDOFF] Starting transfer — summary: %s, lang=%s", summary, self._language)

        self._handoff_active = True

        # Place SIP call to human support in the background.
        # The background task will mute the agent after a short delay.
        asyncio.create_task(self._connect_human_support(context, summary))

        # Return instruction for the model to speak — it will say "please wait"
        # then the background task mutes it before it can say anything else.
        if self._language == "bn":
            return (
                "Say exactly this and nothing else: "
                "'Ektu opekkha korun, ami apnake ekjon support agent er shathe connect korchhi.'"
            )
        else:
            return (
                "Say exactly this and nothing else: "
                "'Please wait while I connect you with a human support agent.'"
            )

    def _set_agent_deaf_mute(self, deaf: bool, mute: bool) -> None:
        """Control the agent's audio input (deaf) and output (mute).

        deaf=True:  unsubscribe from all remote audio tracks (agent can't hear)
        mute=True:  mute the local audio track (agent can't speak)
        """
        # Deaf: unsubscribe from remote participants' audio tracks
        for participant in self._room.remote_participants.values():
            for pub in participant.track_publications.values():
                if pub.kind == rtc.TrackKind.KIND_AUDIO:
                    if isinstance(pub, rtc.RemoteTrackPublication):
                        pub.set_subscribed(not deaf)

        # Mute: mute the actual LocalAudioTrack (not the publication)
        local = self._room.local_participant
        for pub in local.track_publications.values():
            if pub.kind == rtc.TrackKind.KIND_AUDIO and pub.track:
                if mute:
                    pub.track.mute()
                else:
                    pub.track.unmute()

        logger.info("[HANDOFF] Agent deaf=%s mute=%s", deaf, mute)

    async def _connect_human_support(self, context: RunContext, summary: str) -> None:
        """Place SIP call to human support, manage handoff lifecycle."""
        room_name = self._room.name

        # Wait for model to finish speaking "please wait", then mute it
        await asyncio.sleep(5)
        try:
            await context.session.interrupt()
        except Exception:
            pass
        self._set_agent_deaf_mute(deaf=False, mute=True)
        logger.info("[HANDOFF] Agent muted after 'please wait' message")

        try:
            lk_url = LIVEKIT_URL.replace("ws://", "http://").replace("wss://", "https://")
            async with lkapi.LiveKitAPI(
                url=lk_url,
                api_key=LIVEKIT_API_KEY,
                api_secret=LIVEKIT_API_SECRET,
            ) as lk:
                participant_identity = f"{HUMAN_SUPPORT_IDENTITY_PREFIX}{int(time.time())}"

                logger.info(
                    "[HANDOFF] Calling support: %s via trunk %s into room %s",
                    SUPPORT_PHONE_NUMBER, SUPPORT_SIP_TRUNK_ID, room_name,
                )

                await lk.sip.create_sip_participant(
                    lkapi.CreateSIPParticipantRequest(
                        sip_trunk_id=SUPPORT_SIP_TRUNK_ID,
                        sip_call_to=SUPPORT_PHONE_NUMBER,
                        room_name=room_name,
                        participant_identity=participant_identity,
                        participant_name="Human Support Agent",
                        play_dialtone=True,
                    )
                )

                logger.info("[HANDOFF] SIP call placed, waiting for human to pick up...")

                # --- Track human answer/leave ---
                # SIP participant joins the room immediately (before phone answers).
                # track_published fires during ringing (for dialtone audio).
                # The actual answer is detected via participant attributes:
                # sip.callStatus changes to "active" when the phone is picked up.
                human_answered = asyncio.Event()
                human_left = asyncio.Event()

                def _check_sip_active(participant: Any) -> bool:
                    """Check if SIP participant's call is active (answered)."""
                    attrs = participant.attributes or {}
                    status = attrs.get("sip.callStatus", "")
                    logger.info("[HANDOFF] SIP attributes for %s: %s", participant.identity, attrs)
                    return status == "active"

                def _on_participant_attributes_changed(
                    changed_attrs: dict, participant: Any
                ) -> None:
                    if participant.identity.startswith(HUMAN_SUPPORT_IDENTITY_PREFIX):
                        logger.info("[HANDOFF] SIP attributes changed: %s", changed_attrs)
                        if changed_attrs.get("sip.callStatus") == "active" or _check_sip_active(participant):
                            logger.info("[HANDOFF] Human support agent ANSWERED: %s", participant.identity)
                            human_answered.set()

                def _on_participant_disconnected(participant: Any) -> None:
                    if participant.identity.startswith(HUMAN_SUPPORT_IDENTITY_PREFIX):
                        logger.info("[HANDOFF] Human support agent LEFT: %s", participant.identity)
                        human_left.set()

                self._room.on("participant_attributes_changed", _on_participant_attributes_changed)
                self._room.on("participant_disconnected", _on_participant_disconnected)

                # Check if already answered
                for p in self._room.remote_participants.values():
                    if p.identity.startswith(HUMAN_SUPPORT_IDENTITY_PREFIX):
                        if _check_sip_active(p):
                            human_answered.set()

                # Wait up to 60s for human to actually answer the phone
                try:
                    await asyncio.wait_for(human_answered.wait(), timeout=60)
                except asyncio.TimeoutError:
                    logger.warning("[HANDOFF] Human agent never answered (60s timeout)")
                    self._handoff_active = False
                    self._set_agent_deaf_mute(deaf=False, mute=False)
                    return

                # --- Human picked up: unmute and deliver summary ---
                logger.info("[HANDOFF] Human answered, preparing to deliver summary (lang=%s)", self._language)

                # Unmute and wait for audio channel to stabilize
                self._set_agent_deaf_mute(deaf=False, mute=False)
                await asyncio.sleep(2)

                session = context.session
                try:
                    if self._language == "bn":
                        speech = await session.generate_reply(
                            instructions=f"Say exactly this and nothing else: 'Customer er somossa holo: {summary}.'",
                        )
                    else:
                        speech = await session.generate_reply(
                            instructions=f"Say exactly this and nothing else: 'The customer needs help with: {summary}.'",
                        )
                    # Wait for speech to finish playing (not just generating)
                    if speech:
                        await speech.wait_for_playout()
                    logger.info("[HANDOFF] Summary delivered to human agent")
                except Exception as e:
                    logger.error("[HANDOFF] Failed to deliver summary: %s", e)

                # Wait a beat, then go deaf+mute for the handoff
                await asyncio.sleep(1)
                logger.info("[HANDOFF] Agent going deaf+mute during handoff")
                self._set_agent_deaf_mute(deaf=True, mute=True)

                # --- Wait for human to hang up ---
                logger.info("[HANDOFF] Waiting for human to finish...")
                await human_left.wait()

        except Exception as e:
            logger.error("[HANDOFF] Failed during handoff: %s", e)

        # --- Resume agent ---
        logger.info("[HANDOFF] Human left. Restoring agent audio...")
        self._set_agent_deaf_mute(deaf=False, mute=False)
        self._handoff_active = False

        # Small delay to let audio tracks re-establish after undeafening
        await asyncio.sleep(1)

        try:
            session = context.session
            logger.info("[HANDOFF] Resuming with generate_reply (lang=%s)", self._language)
            if self._language == "bn":
                speech = await session.generate_reply(
                    instructions=(
                        "Say exactly this and nothing else: "
                        "'Human support agent call chere diyechen. Apnar aar kono proshno thakle amake bolun.'"
                    ),
                )
            else:
                speech = await session.generate_reply(
                    instructions=(
                        "Say exactly this and nothing else: "
                        "'The human support agent has disconnected. Let me know if you have any other questions.'"
                    ),
                )
            if speech:
                await speech.wait_for_playout()
            logger.info("[HANDOFF] Resume message delivered")
        except Exception as e:
            logger.error("[HANDOFF] Failed to resume agent: %s", e)

    async def _audio_stream_reader(
        self, stream: rtc.AudioStream, buffer: list[bytes], stop_event: asyncio.Event
    ) -> None:
        """Read audio frames from a stream into the buffer until stop_event is set."""
        try:
            async for event in stream:
                if stop_event.is_set():
                    break
                if hasattr(event, 'frame') and event.frame:
                    buffer.append(event.frame.data.tobytes())
        except Exception as e:
            logger.debug("[HANDOFF] Audio stream ended: %s", e)

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

    await _ensure_qdrant_indexed()
    logger.info("[TIMING] Qdrant indexing check — %.2fs", time.monotonic() - t_start)

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    logger.info("[TIMING] connected to room — %.2fs", time.monotonic() - t_start)

    disconnect_event = asyncio.Event()

    t_model = time.monotonic()

    # Voice provider: "openai" (realtime), "local" (pipeline), "qwen" (realtime)
    voice_provider = os.getenv("VOICE_PROVIDER", "openai")

    if voice_provider == "local":
        # --- Local pipeline: STT + LLM + TTS via custom_models server ---
        # Runs on your Mac (M1 Max), accessed via SSH tunnel or VPN.
        # Bengali STT (Whisper), LLM (Qwen3-8B with function calling), TTS (MMS Bengali)
        local_base_url = os.getenv("LOCAL_MODEL_BASE_URL", "http://localhost:8000/v1")
        local_api_key = os.getenv("LOCAL_MODEL_API_KEY", "sk-local-bengali-2026")

        local_stt = openai.STT(
            model="whisper-bengali",
            language="bn",
            base_url=local_base_url,
            api_key=local_api_key,
        )
        local_llm = openai.LLM(
            model="qwen3-8b",
            base_url=local_base_url,
            api_key=local_api_key,
        )
        local_tts = openai.TTS(
            model="tts-1",  # Must use "tts-1" so LiveKit plugin uses simple audio stream
            voice="default",
            response_format="pcm",  # Raw PCM16 24kHz — simplest format, no decoding needed
            base_url=local_base_url,
            api_key=local_api_key,
        )
        logger.info("[TIMING] Local pipeline models configured (base_url=%s) — %.2fs",
                    local_base_url, time.monotonic() - t_model)

        session = AgentSession(
            stt=local_stt,
            llm=local_llm,
            tts=local_tts,
            vad=ctx.proc.userdata["vad"],
        )

        t_session = time.monotonic()
        await session.start(
            agent=BlocksSupportAgent(
                disconnect_event=disconnect_event,
                room=ctx.room,
            ),
            room=ctx.room,
        )
        logger.info("[TIMING] session.start() — %.2fs", time.monotonic() - t_session)

        t_greet = time.monotonic()
        try:
            speech = await session.generate_reply(
                instructions=(
                    "IMPORTANT: You MUST start with 'Assalamu Alaikum' — NEVER say 'Namaskar' or 'Nomoshkar'. "
                    "Say exactly this greeting in Bengali first: "
                    "'Assalamu Alaikum! Ami Blocks Cloud er support assistant. "
                    "Apni ki Banglay shahajjo chan naki English e?' "
                    "Then repeat in English: 'Welcome! I am your Blocks Cloud support assistant. "
                    "Would you prefer Bengali or English?'"
                )
            )
            if speech:
                await speech.wait_for_playout()
            logger.info(
                "[TIMING] greeting generate_reply — %.2fs (total from start: %.2fs)",
                time.monotonic() - t_greet, time.monotonic() - t_start,
            )
        except Exception as e:
            logger.error("[TIMING] greeting FAILED: %s", e)

    elif voice_provider == "qwen" and os.environ.get("DASHSCOPE_API_KEY"):
        # --- Qwen-Omni-Realtime via DashScope (Singapore) ---
        # NOTE: No function calling support.
        qwen_model = os.getenv("QWEN_MODEL", "qwen3-omni-flash-realtime")
        qwen_voice = os.getenv("QWEN_VOICE", "Tina")
        realtime_model = QwenRealtimeModel(
            model=qwen_model,
            voice=qwen_voice,
            temperature=0.7,
        )
        logger.info("[TIMING] Qwen RealtimeModel created — %.2fs", time.monotonic() - t_model)

        session = AgentSession(
            llm=realtime_model,
            vad=ctx.proc.userdata["vad"],
        )

        t_session = time.monotonic()
        await session.start(
            agent=BlocksSupportAgent(
                disconnect_event=disconnect_event,
                room=ctx.room,
            ),
            room=ctx.room,
        )
        logger.info("[TIMING] session.start() — %.2fs", time.monotonic() - t_session)
        logger.info("[TIMING] Qwen ready (total: %.2fs)", time.monotonic() - t_start)

    else:
        # --- OpenAI Realtime (default) ---
        # Supports function calling → RAG, handoff, end_call all work.
        realtime_model = openai.realtime.RealtimeModel(
            model="gpt-realtime-1.5",
            voice="coral",
            temperature=0.7,
        )
        logger.info("[TIMING] OpenAI RealtimeModel created — %.2fs", time.monotonic() - t_model)

        session = AgentSession(
            llm=realtime_model,
            vad=ctx.proc.userdata["vad"],
        )

        t_session = time.monotonic()
        await session.start(
            agent=BlocksSupportAgent(
                disconnect_event=disconnect_event,
                room=ctx.room,
            ),
            room=ctx.room,
        )
        logger.info("[TIMING] session.start() — %.2fs", time.monotonic() - t_session)

        t_greet = time.monotonic()
        await session.generate_reply(
            instructions=(
                "IMPORTANT: You MUST start with 'Assalamu Alaikum' — NEVER say 'Namaskar' or 'Nomoshkar'. "
                "Say exactly this greeting in Bengali first: "
                "'Assalamu Alaikum! Ami Blocks Cloud er support assistant. "
                "Apni ki Banglay shahajjo chan naki English e?' "
                "Then repeat in English: 'Welcome! I am your Blocks Cloud support assistant. "
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
