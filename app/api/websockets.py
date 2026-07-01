import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.session import session_manager
from app.core.agent import agent_orchestrator
from app.adapters.base import get_stt_adapter, get_tts_adapter

router = APIRouter()
logger = logging.getLogger("voice_agent.websockets")

@router.websocket("/ws/call/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket-First entrypoint for real-time audio streams.
    Ingests binary audio chunks from client, pipes through STT -> Agent -> TTS,
    and streams synthetic audio back to client.
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established for session: {session_id}")
    
    # Initialize stateful call session
    session = await session_manager.get_or_create_session(session_id)
    
    # Get decoupled STT & TTS adapters based on provider selection
    stt_adapter = get_stt_adapter()
    tts_adapter = get_tts_adapter()
    
    try:
        # 1. Listen loop for client audio stream
        while True:
            # Receive raw audio chunk (typically PCM or Opus encoded bytes)
            data = await websocket.receive()
            
            if "bytes" in data:
                audio_chunk = data["bytes"]
                
                # 2. Convert Audio Chunk to Text via Async STT Adapter
                # STT uses stream-based or chunk-based transcription
                transcript = await stt_adapter.transcribe_chunk(session_id, audio_chunk)
                
                if transcript and transcript.strip():
                    logger.info(f"[{session_id}] Transcribed user input: {transcript}")
                    
                    # 3. Route to Core Agent Orchestration (with Tool calling & guardrails)
                    agent_response = await agent_orchestrator.process_user_message(session, transcript)
                    logger.info(f"[{session_id}] Agent response: {agent_response}")
                    
                    # 4. Synthesize Agent response text to Audio via TTS Adapter
                    async for audio_out_chunk in tts_adapter.synthesize_stream(agent_response, language=session.language):
                        # 5. Stream audio packets back to client
                        await websocket.send_bytes(audio_out_chunk)
                        
            elif "text" in data:
                import json
                try:
                    payload = json.loads(data["text"])
                    text_content = payload.get("text", "")
                except Exception:
                    text_content = data["text"]
                
                if text_content and text_content.strip():
                    logger.info(f"[{session_id}] Received text command: {text_content}")
                    
                    # 1. Process message with Agent Orchestrator
                    agent_response = await agent_orchestrator.process_user_message(session, text_content)
                    logger.info(f"[{session_id}] Agent response: {agent_response}")
                    
                    # 2. Send text response back to client (so the UI chat updates)
                    await websocket.send_json({"role": "assistant", "content": agent_response})
                    
                    # 3. Stream synthetic TTS audio chunks back to client
                    async for audio_out_chunk in tts_adapter.synthesize_stream(agent_response, language=session.language):
                        await websocket.send_bytes(audio_out_chunk)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error in session {session_id}: {str(e)}", exc_info=True)
    finally:
        # Mark session as inactive but do not delete state immediately 
        # (allows reconnect or cleanup after timeout)
        await session_manager.deactivate_session(session_id)
