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

from intent.models import ConversationIntent

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
                {"user_input": message["content"], "intent": intent.dict()}
            )
            
            # Route to plugins via message bus
            response = await route_to_plugins(intent, message)
            
            # Send response back to frontend
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

async def route_to_plugins(intent, message: Dict[str, Any]) -> Dict[str, Any]:
    """Route intent to appropriate plugins and return response"""
    # This is where the magic happens - orchestrating plugin communication
    # Based on the intent, route to appropriate plugins
    
    try:
        if intent.type == "mission_request":
            # Route to GitHub Integration plugin
            response = await message_bus.request_response(
                "github_integration",
                "create_mission",
                {"intent": intent.dict(), "message": message}
            )
        elif intent.type == "status_check":
            # Route to appropriate plugin based on what status is requested
            response = await handle_status_request(intent, message)
        elif intent.type == "question":
            # Route to appropriate knowledge source
            response = await handle_question(intent, message)
        elif intent.type == "command":
            # Handle direct commands
            response = await handle_command(intent, message)
        elif intent.type == "discussion":
            # Handle architectural discussions
            response = await handle_discussion(intent, message)
        elif intent.type == "troubleshooting":
            # Handle debugging and troubleshooting
            response = await handle_troubleshooting(intent, message)
        else:
            # Default response for unhandled intents
            response = {
                "type": "response",
                "content": f"I understand you're asking about something ({intent.type}), but I'm not sure how to help with that yet. Can you be more specific?",
                "intent": intent.dict(),
                "confidence": intent.confidence
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error routing intent: {e}")
        return {
            "type": "error",
            "content": "I encountered an error while processing your request. Let me try to help in a different way.",
            "intent": intent.dict() if hasattr(intent, 'dict') else str(intent),
            "error": str(e)
        }

async def handle_status_request(intent: ConversationIntent, message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle status check requests"""
    try:
        # Determine what status is being requested
        user_input = message["content"].lower()
        
        if "mission" in user_input:
            # Route to GitHub Integration for mission status
            if "github_integration" in intent.requires_plugins:
                response = await message_bus.request_response(
                    "github_integration",
                    "get_mission_status",
                    {"intent": intent.dict(), "message": message}
                )
            else:
                response = {
                    "type": "status_response",
                    "content": "To check mission status, I'll need to connect to GitHub. Let me check the available missions for you.",
                    "intent": intent.dict()
                }
        elif "system" in user_input or "health" in user_input:
            # Return system health status
            health_status = await get_system_health()
            response = {
                "type": "status_response",
                "content": f"System Status: {health_status['status']}\n\nComponents:\n" + 
                          "\n".join([f"- {k}: {v}" for k, v in health_status['components'].items()]),
                "intent": intent.dict(),
                "data": health_status
            }
        else:
            response = {
                "type": "status_response", 
                "content": "I can check status for missions, system health, or specific components. What would you like to know about?",
                "intent": intent.dict()
            }
            
        return response
        
    except Exception as e:
        logger.error(f"Error handling status request: {e}")
        return {
            "type": "error",
            "content": "I had trouble checking the status. Could you be more specific about what you'd like to know?",
            "intent": intent.dict(),
            "error": str(e)
        }

async def handle_question(intent: ConversationIntent, message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle general questions"""
    try:
        user_input = message["content"].lower()
        
        if "how" in user_input and ("work" in user_input or "works" in user_input):
            # Architecture/system questions
            response = {
                "type": "answer",
                "content": "I'm Riker, your AI development assistant. I can help you manage missions, check system status, create new features, and discuss architectural decisions. I coordinate between different plugins like GitHub Integration, Memory Manager, and Config Manager to help you build software more efficiently.\n\nWhat would you like to know more about?",
                "intent": intent.dict()
            }
        elif "plugin" in user_input:
            # Plugin information
            plugin_status = await plugin_registry.get_status()
            response = {
                "type": "answer",
                "content": f"Currently available plugins:\n" + 
                          "\n".join([f"- {name}: {status}" for name, status in plugin_status.items()]),
                "intent": intent.dict(),
                "data": plugin_status
            }
        else:
            # General questions - try to be helpful
            response = {
                "type": "answer",
                "content": "I'm here to help! I can assist with:\n\n• Creating and managing development missions\n• Checking system and mission status\n• Discussing architecture and implementation approaches\n• Troubleshooting issues\n\nWhat specific question do you have?",
                "intent": intent.dict()
            }
            
        return response
        
    except Exception as e:
        logger.error(f"Error handling question: {e}")
        return {
            "type": "error", 
            "content": "I had trouble processing your question. Could you rephrase it?",
            "intent": intent.dict(),
            "error": str(e)
        }

async def handle_command(intent: ConversationIntent, message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle direct commands"""
    try:
        # Parse commands and route to appropriate plugins
        user_input = message["content"].lower()
        
        if "create mission" in user_input or "new mission" in user_input:
            # Route to GitHub Integration
            response = await message_bus.request_response(
                "github_integration",
                "create_mission",
                {"intent": intent.dict(), "message": message}
            )
        else:
            response = {
                "type": "command_response",
                "content": "I can help with commands like 'create mission', 'show status', etc. What command would you like to run?",
                "intent": intent.dict()
            }
            
        return response
        
    except Exception as e:
        logger.error(f"Error handling command: {e}")
        return {
            "type": "error",
            "content": "I had trouble executing that command. Please try rephrasing it.",
            "intent": intent.dict(),
            "error": str(e)
        }

async def handle_discussion(intent: ConversationIntent, message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle architectural discussions"""
    return {
        "type": "discussion_response",
        "content": "I'd be happy to discuss architecture, design decisions, or implementation approaches with you. What aspect would you like to explore?",
        "intent": intent.dict()
    }

async def handle_troubleshooting(intent: ConversationIntent, message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle debugging and troubleshooting"""
    return {
        "type": "troubleshooting_response", 
        "content": "I can help debug issues, check system health, or troubleshoot problems. What specific issue are you encountering?",
        "intent": intent.dict()
    }

async def get_system_health() -> Dict[str, Any]:
    """Get current system health status"""
    try:
        return {
            "status": "operational",
            "components": {
                "websocket": "ready",
                "message_bus": await message_bus.health_check(),
                "plugins": await plugin_registry.get_status(),
                "memory": await conversation_memory.health_check()
            }
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {
            "status": "degraded",
            "components": {
                "error": str(e)
            }
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
