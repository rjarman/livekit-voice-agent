# LiveKit + n8n Self-Hosted Stack

A complete self-hosted stack for AI-powered voice/video communication with workflow automation.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Services                                 │
├─────────────────────────────────────────────────────────────────┤
│  React App (:3000)  │  Dashboard (:8000)  │  n8n (:5678)        │
├─────────────────────────────────────────────────────────────────┤
│                    Token Server (:3001)                          │
├─────────────────────────────────────────────────────────────────┤
│                 LiveKit Server (:7880-7882)                      │
├─────────────────────────────────────────────────────────────────┤
│  LiveKit Agent  │  PostgreSQL  │  Qdrant (:6333)                │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Services

| Service | Port | Description |
|---------|------|-------------|
| **livekit** | 7880, 7881, 7882/udp | WebRTC media server |
| **livekit-react-app** | 3000 | Video conferencing UI |
| **livekit-token-server** | 3001 | Token generation API |
| **livekit-agent** | - | AI voice assistant (STT/LLM/TTS) |
| **livekit-dashboard** | 8000 | Admin dashboard |
| **n8n** | 5678 | Workflow automation |
| **postgres** | 5432 | Database for n8n |
| **qdrant** | 6333, 6334 | Vector database |

## 🚀 Quick Setup

### 1. Clone and Navigate
```bash
git clone https://github.com/rjarman/livekit-voice-agent.git
cd livekit-voice-agent
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` with your values:
```bash
# Required - Your server's public IP or domain
SERVER_IP_ADDRESS=<server-ip-address or domain>

# Generate secure passwords
POSTGRES_PASSWORD=$(openssl rand -base64 24)
N8N_ENCRYPTION_KEY=$(openssl rand -base64 24)

# LiveKit credentials (generate or use existing)
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Dashboard admin
LIVEKIT_DASHBOARD_USERNAME=admin
LIVEKIT_DASHBOARD_PASSWORD=your-secure-password
LIVEKIT_DASHBOARD_SECRET_KEY=$(openssl rand -hex 32)

# AI Service API Keys (free tiers available)
ASSEMBLYAI_API_KEY=xxx    # https://www.assemblyai.com
GROQ_API_KEY=xxx          # https://console.groq.com
CARTESIA_API_KEY=xxx      # https://play.cartesia.ai

# Qdrant
QDRANT_API_KEY=your-qdrant-key
```

### 3. Generate LiveKit Credentials (if needed)
```bash
# Using openssl
echo "API Key: API$(openssl rand -hex 7)"
echo "API Secret: $(openssl rand -base64 32)"
```

### 4. Start Services
```bash
docker compose up -d
```

### 5. Verify
```bash
docker compose ps
docker compose logs -f
```

## 🔗 Access URLs

After deployment (replace with your server IP/domain):

| Service | URL |
|---------|-----|
| React App | http://\<server-ip\>:3000 |
| Dashboard | http://\<server-ip\>:8000 |
| n8n | http://\<server-ip\>:5678 |
| Token API | http://\<server-ip\>:3001/token |

## 🎙️ AI Voice Agent

The agent uses free-tier AI services:

| Function | Provider | Free Tier |
|----------|----------|-----------|
| Speech-to-Text | AssemblyAI | 100 hours |
| LLM | Groq (Llama 3.1) | Generous limits |
| Text-to-Speech | Cartesia | Free tier |

## 🔧 Useful Commands

```bash
# View logs
docker compose logs -f livekit-agent

# Rebuild agent after changes
docker compose build livekit-agent
docker compose up -d livekit-agent

# Rebuild react app after changes
docker compose build livekit-react-app
docker compose up -d livekit-react-app

# Stop all
docker compose down

# Stop and remove volumes (data loss!)
docker compose down -v
```

## 📁 File Structure

```
livekit-voice-agent/
├── docker-compose.yml      # Main orchestration
├── .env.example            # Environment template
├── .env                    # Your configuration (create this)
├── livekit.yaml            # LiveKit server config
├── livekit-token-server/   # Token generation service
│   ├── server.js
│   └── package.json
├── livekit-agent/          # AI voice agent
│   ├── agent.py
│   ├── pyproject.toml
│   └── Dockerfile
└── livekit-react-app/      # React frontend
    ├── src/
    ├── Dockerfile
    └── nginx.conf
```

## 🔐 HTTPS & Media Access

Browsers require **HTTPS** (or localhost) to access camera/microphone. If you're using HTTP with an IP address, you'll see:

```
Error: Accessing media devices is available only in secure contexts
```

### Solution: Chrome Flags (Development/POC)

1. Open Chrome and go to:
   ```
   chrome://flags/#unsafely-treat-insecure-origin-as-secure
   ```

2. Paste your server URLs (comma-separated):
   ```
   http://<server-ip>:3000,http://<server-ip>:7880,http://<server-ip>:3001
   ```

3. Set to **Enabled**

4. Click **Relaunch**

### Production: Use HTTPS

For production, set up a domain with SSL using [Caddy](https://caddyserver.com/) or a reverse proxy.

## ⚠️ Firewall Ports

Ensure these ports are open on your server:

| Port | Protocol | Service |
|------|----------|---------|
| 3000 | TCP | React App |
| 3001 | TCP | Token Server |
| 5678 | TCP | n8n |
| 6333-6334 | TCP | Qdrant |
| 7880 | TCP | LiveKit HTTP |
| 7881 | TCP | LiveKit TCP |
| 7882 | UDP | LiveKit WebRTC |
| 8000 | TCP | Dashboard |

## 📚 Resources

- [LiveKit Docs](https://docs.livekit.io/)
- [LiveKit Dashboard](https://github.com/thinhdanggroup/livekit-dashboard)
- [n8n Docs](https://docs.n8n.io/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
