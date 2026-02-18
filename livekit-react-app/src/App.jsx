import { useState, useCallback } from 'react';
import {
  LiveKitRoom,
  VideoConference,
  RoomAudioRenderer,
} from '@livekit/components-react';

// Detect if we're on HTTPS (domain) or HTTP (IP)
const isSecure = window.location.protocol === 'https:';

// When on HTTPS, always use the current hostname (domain)
// When on HTTP, use env var or fallback to hostname
const SERVER_HOST = isSecure 
  ? window.location.hostname 
  : (import.meta.env.VITE_SERVER_IP_ADDRESS || window.location.hostname);

// Use WSS/HTTPS when on secure connection, WS/HTTP otherwise
const LIVEKIT_URL = isSecure 
  ? `wss://${SERVER_HOST}/livekit`
  : `ws://${SERVER_HOST}:7880`;

// Token server: use /api path when on domain (proxied by Caddy), direct port when on IP
const TOKEN_SERVER_URL = isSecure
  ? `${window.location.origin}/api`
  : `http://${SERVER_HOST}:3001`;

function App() {
  const [token, setToken] = useState('');
  const [roomName, setRoomName] = useState('');
  const [userName, setUserName] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState('');

  const handleJoin = useCallback(async (e) => {
    e.preventDefault();
    
    if (!roomName.trim() || !userName.trim()) {
      setError('Please enter both room name and your name');
      return;
    }

    setIsConnecting(true);
    setError('');

    try {
      const response = await fetch(`${TOKEN_SERVER_URL}/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          roomName: roomName.trim(),
          participantName: userName.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get token from server');
      }

      const data = await response.json();
      setToken(data.token);
    } catch (err) {
      console.error('Error joining room:', err);
      setError(`Failed to join: ${err.message}. Make sure the token server is running.`);
      setIsConnecting(false);
    }
  }, [roomName, userName]);

  const handleDisconnect = useCallback(() => {
    setToken('');
    setIsConnecting(false);
  }, []);

  // Pre-join form
  if (!token) {
    return (
      <div className="pre-join-container">
        <div className="pre-join-card">
          <h1>LiveKit Room</h1>
          <p className="subtitle">Join a video conference</p>
          
          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleJoin}>
            <div className="form-group">
              <label htmlFor="roomName">Room Name</label>
              <input
                id="roomName"
                type="text"
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
                placeholder="Enter room name..."
                disabled={isConnecting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="userName">Your Name</label>
              <input
                id="userName"
                type="text"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                placeholder="Enter your name..."
                disabled={isConnecting}
              />
            </div>

            <button type="submit" className="join-button" disabled={isConnecting}>
              {isConnecting ? 'Connecting...' : 'Join Room'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Video room
  return (
    <div className="video-room-container">
      <LiveKitRoom
        serverUrl={LIVEKIT_URL}
        token={token}
        connect={true}
        onDisconnected={handleDisconnect}
        audio={true}
        video={true}
        data-lk-theme="default"
      >
        <VideoConference />
        <RoomAudioRenderer />
      </LiveKitRoom>
    </div>
  );
}

export default App;
