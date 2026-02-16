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
COPY pyproject.toml .
COPY agent.py .

# Install dependencies with uv
RUN uv sync --no-dev

# Download Silero VAD model during build
RUN uv run python -c "from livekit.plugins import silero; silero.VAD.load()"

# Run the agent
CMD ["uv", "run", "python", "agent.py", "start"]
