"""
WebSocket connection management
Handles real-time bidirectional communication between frontend and backend

Architecture Decision: Centralized connection management allows for:
- Broadcasting messages to multiple clients
- Managing connection lifecycle
- Implementing connection pooling and health checks
"""
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
import logging
from datetime import datetime

class ConnectionManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        # Generate client ID if not provided
        if not client_id:
            client_id = f"client_{len(self.active_connections)}_{datetime.now().timestamp()}"
        
        # Store connection and metadata
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "conversation_id": None
        }
        
        logging.info(f"Client {client_id} connected")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "client_id": client_id,
            "message": "Welcome to SIDHE! Ready to engage."
        }, websocket)
        
        return client_id
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        # Find and remove the connection
        client_id = None
        for cid, conn in self.active_connections.items():
            if conn == websocket:
                client_id = cid
                break
        
        if client_id:
            del self.active_connections[client_id]
            del self.connection_metadata[client_id]
            logging.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logging.error(f"Error sending message: {e}")
    
    async def send_message_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send a message to a specific client by ID"""
        if client_id in self.active_connections:
            await self.send_personal_message(message, self.active_connections[client_id])
        else:
            logging.warning(f"Client {client_id} not found")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        for client_id, connection in self.active_connections.items():
            await self.send_personal_message(message, connection)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_client_metadata(self, client_id: str) -> Dict[str, Any]:
        """Get metadata for a specific client"""
        return self.connection_metadata.get(client_id, {})
    
    def update_client_activity(self, client_id: str, conversation_id: str = None):
        """Update client activity timestamp and conversation ID"""
        if client_id in self.connection_metadata:
            self.connection_metadata[client_id]["last_activity"] = datetime.now()
            if conversation_id:
                self.connection_metadata[client_id]["conversation_id"] = conversation_id