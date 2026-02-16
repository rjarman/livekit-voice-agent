import logging
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    JobRequest,
    WorkerOptions,
    cli,
)
from livekit.plugins import assemblyai, groq, cartesia, silero

load_dotenv()

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

# Track rooms that already have an agent (shared across processes via module)
active_rooms = set()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant. The user is interacting with you via voice.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.""",
        )


def prewarm(proc: JobProcess):
    """Preload VAD model for faster startup"""
    proc.userdata["vad"] = silero.VAD.load()


async def request_fnc(req: JobRequest) -> None:
    """Accept job request only if room doesn't already have an agent"""
    room_name = req.room.name
    
    if room_name in active_rooms:
        logger.info(f"Rejecting duplicate job for room: {room_name}")
        await req.reject()
        return
    
    logger.info(f"Accepting job request for room: {room_name}")
    active_rooms.add(room_name)
    await req.accept()


async def entrypoint(ctx: JobContext):
    """Main entry point when job is accepted"""
    room_name = ctx.room.name
    logger.info(f"Agent starting in room: {room_name}")
    
    try:
        # Connect to the room
        await ctx.connect()
        
        session = AgentSession(
            stt=assemblyai.STT(),
            llm=groq.LLM(model="llama-3.1-8b-instant"),
            tts=cartesia.TTS(),
            vad=ctx.proc.userdata["vad"],
        )

        await session.start(
            agent=Assistant(),
            room=ctx.room,
        )
        
        logger.info(f"Agent session started in room: {room_name}")
    finally:
        # Clean up when agent leaves
        active_rooms.discard(room_name)
        logger.info(f"Agent left room: {room_name}")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            request_fnc=request_fnc,
        ),
    )
