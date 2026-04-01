const express = require('express');
const cors = require('cors');
const { AccessToken, RoomServiceClient, AgentDispatchClient, SipClient, SIPParticipantInfo } = require('livekit-server-sdk');

const app = express();
app.use(cors());
app.use(express.json());

const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY;
const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_WS_URL = process.env.LIVEKIT_URL;
const LIVEKIT_URL = LIVEKIT_WS_URL.replace('ws://', 'http://').replace('wss://', 'https://');
const PORT = process.env.PORT || 3001;

const roomService = new RoomServiceClient(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET);
const agentDispatch = new AgentDispatchClient(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET);
const sipClient = new SipClient(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET);

// Track rooms with dispatched agents (prevent duplicates)
const dispatchedRooms = new Map(); // roomName -> dispatchId

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.post('/token', async (req, res) => {
  try {
    const { roomName, participantName } = req.body;

    if (!roomName || !participantName) {
      return res.status(400).json({ error: 'roomName and participantName are required' });
    }

    // Create access token
    const at = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
      identity: participantName,
      name: participantName,
      ttl: '1h',
    });

    at.addGrant({
      roomJoin: true,
      room: roomName,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    });

    const token = await at.toJwt();

    // Create room if needed
    try {
      await roomService.createRoom({ name: roomName });
      console.log(`Room created: ${roomName}`);
    } catch (e) {
      // Room exists
    }

    // Dispatch agent ONLY if we haven't already for this room
    if (!dispatchedRooms.has(roomName)) {
      // Mark as dispatching BEFORE the async call to prevent race conditions
      dispatchedRooms.set(roomName, 'pending');
      
      try {
        const dispatch = await agentDispatch.createDispatch(roomName, 'apple-seller-agent-bn');
        dispatchedRooms.set(roomName, dispatch?.dispatchId || 'dispatched');
        console.log(`Agent dispatched to room: ${roomName}`);
        
        // Clean up after 1 hour
        setTimeout(() => dispatchedRooms.delete(roomName), 60 * 60 * 1000);
      } catch (e) {
        dispatchedRooms.delete(roomName);
        console.log(`Dispatch error: ${e.message}`);
      }
    } else {
      console.log(`Skipping dispatch - agent already in room: ${roomName}`);
    }

    res.json({ token, roomName, participantName });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'Failed to generate token' });
  }
});

app.get('/token', async (req, res) => {
  try {
    const { room, identity } = req.query;

    if (!room || !identity) {
      return res.status(400).json({ error: 'room and identity query params are required' });
    }

    const at = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
      identity,
      name: identity,
      ttl: '1h',
    });

    at.addGrant({
      roomJoin: true,
      room,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    });

    const token = await at.toJwt();
    res.json({ token });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'Failed to generate token' });
  }
});

app.post('/sip/call', async (req, res) => {
  try {
    const { roomName, phoneNumber, sipTrunkId } = req.body;

    if (!roomName || !phoneNumber || !sipTrunkId) {
      return res.status(400).json({
        error: 'roomName, phoneNumber, and sipTrunkId are required',
      });
    }

    await roomService.createRoom({ name: roomName }).catch(() => {});

    try {
      await agentDispatch.createDispatch(roomName, 'apple-seller-agent-bn');
      console.log(`Agent dispatched to room: ${roomName}`);
    } catch (e) {
      console.log(`Agent dispatch note: ${e.message}`);
    }

    await new Promise(resolve => setTimeout(resolve, 2000));

    const participant = await sipClient.createSipParticipant(
      sipTrunkId,
      phoneNumber,
      roomName,
      {
        participantIdentity: `phone-${phoneNumber}`,
        participantName: `Phone ${phoneNumber}`,
        playDialtone: true,
      }
    );

    console.log(`Outbound call to ${phoneNumber} in room ${roomName}`);
    res.json({ success: true, participant });
  } catch (error) {
    console.error('SIP call error:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/sip/trunks', async (req, res) => {
  try {
    const trunks = await sipClient.listSipOutboundTrunk();
    res.json({ trunks });
  } catch (error) {
    console.error('Error listing trunks:', error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Token server running on port ${PORT}`);
  console.log(`LiveKit URL: ${LIVEKIT_URL}`);
});
