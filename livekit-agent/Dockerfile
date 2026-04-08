FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY livekit-agent/pyproject.toml .
COPY livekit-agent/voice-agent.py .
COPY livekit-agent/apple-seller-agent.py .
COPY livekit-agent/apple-seller-agent-bn.py .
COPY livekit-agent/blocks-support-agent.py .

# Install dependencies with uv
RUN uv sync --no-dev

# Install Qwen realtime plugin
COPY livekit-plugins-qwen/ /tmp/livekit-plugins-qwen/
RUN uv pip install /tmp/livekit-plugins-qwen/ && rm -rf /tmp/livekit-plugins-qwen/

# Download Silero VAD model during build
RUN uv run python -c "from livekit.plugins import silero; silero.VAD.load()"

# Default: run voice agent (override in docker-compose for apple-seller-agent)
CMD ["uv", "run", "python", "voice-agent.py", "start"]
