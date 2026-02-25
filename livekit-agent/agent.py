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
    RoomInputOptions,
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
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    room_name = ctx.room.name
    logger.info(f"Agent connecting to room: {room_name}")

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info(f"Agent connected to room: {room_name}, waiting for participant...")

    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}, starting agent session")

    session = AgentSession(
        stt=assemblyai.STT(),
        llm=groq.LLM(model="llama-3.1-8b-instant"),
        tts=cartesia.TTS(),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input=RoomInputOptions(participant=participant),
    )

    logger.info(f"Agent session started in room: {room_name}")
    await session.say("Hello! How can I help you today?")
    logger.info("Greeting sent")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="voice-agent",
        ),
    )