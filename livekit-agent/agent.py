import asyncio
import logging
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    AutoSubscribe,
)
from livekit.plugins import assemblyai, groq, cartesia, silero

load_dotenv()

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)


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


async def entrypoint(ctx: JobContext):
    """Main entry point - agent joins every room automatically"""
    room_name = ctx.room.name
    logger.info(f"Agent connecting to room: {room_name}")
    
    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    logger.info(f"Agent connected to room: {room_name}, waiting for participant...")
    
    # Wait for a participant to join (don't start until someone is there)
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}, starting agent session")
    
    try:
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
        
        # Say hello to the participant
        await session.say("Hello! How can I help you today?")
        logger.info("Greeting sent")
        
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise
    
    # Keep running until disconnected
    while ctx.room.connection_state.name == "CONN_CONNECTED":
        await asyncio.sleep(1)
    
    logger.info(f"Agent leaving room: {room_name}")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="voice-assistant",
        ),
    )
