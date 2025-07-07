"""
Conversation Engine Backend - Foundation
FastAPI application with WebSocket support for real-time communication

This is the central orchestrator for SIDHE's conversational AI system.
It coordinates between plugins through a Redis message bus and provides
a WebSocket interface for real-time communication with the React frontend.

Architecture Decision: Located at src/voice_of_wisdom/ (not src/plugins/)
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

from config.settings import settings

# Initialize logger
logger = logging.getLogger(__name__)
from websocket.connection import ConnectionManager
from intent.parser import IntentParser
from bus.publisher import MessageBus
from memory.integration import ConversationMemory
# Disable plugin registry for now to eliminate errors
PluginRegistry = None

# Settings imported from config module

# Initialize FastAPI app
app = FastAPI(
    title="SIDHE Conversation Engine",
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

# Initialize lightweight components
connection_manager = ConnectionManager()

# Initialize heavy components during startup
intent_parser = None
message_bus = None
conversation_memory = None
plugin_registry = None

@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup"""
    global intent_parser, message_bus, conversation_memory, plugin_registry
    
    # Initialize components during startup
    intent_parser = IntentParser()
    message_bus = MessageBus()
    # Temporarily disable memory to fix core conversation functionality
    # conversation_memory = ConversationMemory()
    plugin_registry = PluginRegistry() if PluginRegistry else None
    
    # Temporarily disable message bus Redis initialization
    # await message_bus.initialize()
    if plugin_registry:
        await plugin_registry.discover_plugins()
    logging.info("Conversation Engine startup complete")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "SIDHE Conversation Engine - Ready to engage!"}

@app.get("/health")
async def health_check():
    """Detailed health check with component status"""
    return {
        "status": "enchanted",
        "components": {
            "websocket": "ready",
            "message_bus": await message_bus.health_check(),
            "plugins": await plugin_registry.get_status() if plugin_registry else "not_available",
            "memory": await conversation_memory.health_check() if conversation_memory else "disabled"
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint with direct conversation processing"""
    await websocket.accept()
    logger.info("🔥 WebSocket handler - connection accepted")
    
    # Send connection established message
    await websocket.send_text(json.dumps({
        "type": "connection_established",
        "message": "Connected to SIDHE - Ready for conversation!"
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"🔥 HANDLER - Received: {data}")
            
            try:
                message = json.loads(data)
                user_input = message.get("content", "")
                conversation_id = message.get("conversation_id", "default")
                
                # Process with intent parser and generate AI response
                if intent_parser:
                    logger.info(f"🧠 Processing message: {user_input}")
                    intent = await intent_parser.parse_intent(user_input, conversation_id)
                    logger.info(f"✅ Intent parsed: {intent.type}")
                    
                    # Generate response based on intent
                    response = await route_to_plugins(intent, message)
                    logger.info(f"📤 Sending response: {response}")
                    
                    await websocket.send_text(json.dumps(response))
                else:
                    # Fallback response if intent parser not available
                    await websocket.send_text(json.dumps({
                        "type": "response",
                        "content": f"I received your message: '{user_input}' - but my intent parser is not available right now."
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "content": "I received your message but couldn't parse it properly. Please try again."
                }))
            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "content": f"I encountered an error processing your message: {str(e)}"
                }))
            
    except WebSocketDisconnect:
        logger.info("🔥 WebSocket disconnected")

@app.websocket("/ws_old")
async def websocket_endpoint_old(websocket: WebSocket):
    """Main WebSocket endpoint for real-time communication"""
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            logger.info(f"🎯 Received WebSocket message: {data}")
            
            try:
                message = json.loads(data)
                logger.info(f"📝 Parsed message: {message}")
                
                # Simple response for testing
                if not intent_parser:
                    logger.error("Intent parser not initialized")
                    response = {
                        "type": "error",
                        "content": "Intent parser not available"
                    }
                else:
                    # Parse intent and route to appropriate handler
                    logger.info("🧠 Parsing intent...")
                    intent = await intent_parser.parse_intent(
                        message["content"], 
                        message.get("conversation_id")
                    )
                    logger.info(f"✅ Intent parsed: {intent.type}")
                    
                    # Route to plugins via message bus
                    logger.info("🔄 Routing to plugins...")
                    response = await route_to_plugins(intent, message)
                    logger.info(f"📤 Generated response: {response}")
                
                # Send response back to frontend
                await websocket.send_text(json.dumps(response))
                logger.info("✅ Response sent to frontend")
                
            except Exception as e:
                logger.error(f"❌ Error processing WebSocket message: {e}")
                import traceback
                traceback.print_exc()
                
                error_response = {
                    "type": "error",
                    "content": f"I encountered an error processing your message: {str(e)}",
                    "error": str(e)
                }
                await websocket.send_text(json.dumps(error_response))
            
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()

async def route_to_plugins(intent, message: Dict[str, Any]) -> Dict[str, Any]:
    """Route intent to appropriate plugins and return response"""
    # This is where the magic happens - orchestrating plugin communication
    # Based on the intent, route to appropriate plugins
    
    try:
        if intent.type == "quest_request":
            # Route to GitHub Integration plugin
            response = await message_bus.request_response(
                "quest_tracker",
                "create_quest",
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
        
        if "quest" in user_input:
            # Route to GitHub Integration for quest status
            if "quest_tracker" in intent.requires_plugins:
                response = await message_bus.request_response(
                    "quest_tracker",
                    "get_quest_status",
                    {"intent": intent.dict(), "message": message}
                )
            else:
                response = {
                    "type": "status_response",
                    "content": "To check quest status, I'll need to connect to GitHub. Let me check the available missions for you.",
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
                "content": "I'm SIDHE, your AI development assistant. I can help you manage missions, check system status, create new features, and discuss architectural decisions. I coordinate between different plugins like GitHub Integration, Memory Manager, and Config Manager to help you build software more efficiently.\n\nWhat would you like to know more about?",
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
                "content": "I'm here to help! I can assist with:\n\n• Creating and managing development missions\n• Checking system and quest status\n• Discussing architecture and implementation approaches\n• Troubleshooting issues\n\nWhat specific question do you have?",
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
        
        if "create quest" in user_input or "new quest" in user_input:
            # Route to GitHub Integration
            response = await message_bus.request_response(
                "quest_tracker",
                "create_quest",
                {"intent": intent.dict(), "message": message}
            )
        else:
            response = {
                "type": "command_response",
                "content": "I can help with commands like 'create quest', 'show status', etc. What command would you like to run?",
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
            "status": "enchanted",
            "components": {
                "websocket": "ready",
                "message_bus": await message_bus.health_check(),
                "plugins": await plugin_registry.get_status() if plugin_registry else "not_available",
                "memory": await conversation_memory.health_check() if conversation_memory else "disabled"
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
