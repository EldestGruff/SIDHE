"""
Conversation Engine Backend - Foundation
FastAPI application with WebSocket support for real-time communication

This is the central orchestrator for Riker's conversational AI system.
It coordinates between plugins through a Redis message bus and provides
a WebSocket interface for real-time communication with the React frontend.

Architecture Decision: Located at src/conversation_engine/ (not src/plugins/)
because this is the main application that orchestrates all plugins, not a plugin itself.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
from typing import Dict, Any
import uvicorn

from config.settings import Settings
from websocket.connection import ConnectionManager
from intent.parser import IntentParser
from bus.publisher import MessageBus
from memory.integration import ConversationMemory
from plugins.registry import PluginRegistry

# Initialize settings
settings = Settings()

# Initialize FastAPI app
app = FastAPI(
    title="Riker Conversation Engine",
    description="Central orchestrator for conversational AI development",
    version="0.1.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
connection_manager = ConnectionManager()
intent_parser = IntentParser()
message_bus = MessageBus()
conversation_memory = ConversationMemory()
plugin_registry = PluginRegistry()

@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup"""
    await message_bus.initialize()
    await plugin_registry.discover_plugins()
    logging.info("Conversation Engine startup complete")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Riker Conversation Engine - Ready to engage!"}

@app.get("/health")
async def health_check():
    """Detailed health check with component status"""
    return {
        "status": "operational",
        "components": {
            "websocket": "ready",
            "message_bus": await message_bus.health_check(),
            "plugins": await plugin_registry.get_status(),
            "memory": await conversation_memory.health_check()
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time communication"""
    await connection_manager.connect(websocket)
    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Parse intent and route to appropriate handler
            intent = await intent_parser.parse_intent(
                message["content"], 
                message.get("conversation_id")
            )
            
            # Store conversation turn
            await conversation_memory.store_turn(
                message.get("conversation_id"),
                {"user_input": message["content"], "intent": intent}
            )
            
            # Route to plugins via message bus
            response = await route_to_plugins(intent, message)
            
            # Send response back to frontend
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

async def route_to_plugins(intent: Dict[str, Any], message: Dict[str, Any]) -> Dict[str, Any]:
    """Route intent to appropriate plugins and return response"""
    # This is where the magic happens - orchestrating plugin communication
    # Based on the intent, route to appropriate plugins
    
    if intent["type"] == "mission_request":
        # Route to GitHub Integration plugin
        response = await message_bus.request_response(
            "github_integration",
            "create_mission",
            {"intent": intent, "message": message}
        )
    elif intent["type"] == "status_check":
        # Route to appropriate plugin based on what status is requested
        response = await handle_status_request(intent, message)
    elif intent["type"] == "question":
        # Route to appropriate knowledge source
        response = await handle_question(intent, message)
    else:
        # Default response for unhandled intents
        response = {
            "type": "response",
            "content": "I understand you're asking about something, but I'm not sure how to help with that yet. Can you be more specific?",
            "intent": intent
        }
    
    return response

async def handle_status_request(intent: Dict[str, Any], message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle status check requests"""
    # Determine what status is being requested and route appropriately
    return {
        "type": "status_response",
        "content": "Status check functionality will be implemented by Claude Code",
        "intent": intent
    }

async def handle_question(intent: Dict[str, Any], message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle general questions"""
    # Route to appropriate knowledge source or plugin
    return {
        "type": "answer",
        "content": "Question handling will be implemented by Claude Code",
        "intent": intent
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
