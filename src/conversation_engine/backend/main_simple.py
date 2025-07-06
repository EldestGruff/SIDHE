"""
Simple FastAPI backend for WebSocket testing
Minimal implementation to get WebSocket connection working
"""
import os
import json
import logging
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import redis
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Riker Conversation Engine - Simple", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection for message bus
redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379')
try:
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    logger.info(f"✅ Connected to Redis at {redis_url}")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}")
    redis_client = None

# Store active WebSocket connections
active_connections = []

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")

manager = ConnectionManager()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "redis_connected": redis_client is not None,
        "active_connections": len(manager.active_connections)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    
    # Send connection established message
    await manager.send_personal_message(
        json.dumps({
            "type": "connection_established",
            "message": "Connected to Riker Conversation Engine",
            "timestamp": datetime.now().isoformat()
        }),
        websocket
    )
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            logger.info(f"Received message: {data}")
            
            try:
                # Parse the incoming message
                message_data = json.loads(data)
                content = message_data.get('content', '')
                conversation_id = message_data.get('conversation_id', 'default')
                
                # Echo back a simple response
                response = {
                    "type": "response",
                    "content": f"Echo: {content}",
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat(),
                    "intent": "echo"
                }
                
                # Send response back to client
                await manager.send_personal_message(
                    json.dumps(response),
                    websocket
                )
                
                # Store in Redis if available
                if redis_client:
                    try:
                        key = f"riker:message:{conversation_id}:{datetime.now().timestamp()}"
                        redis_client.setex(key, 3600, json.dumps({
                            "user_message": content,
                            "bot_response": response["content"],
                            "timestamp": response["timestamp"]
                        }))
                    except Exception as e:
                        logger.warning(f"Failed to store in Redis: {e}")
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error", 
                        "message": "Invalid JSON format"
                    }),
                    websocket
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error", 
                        "message": "Internal server error"
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )