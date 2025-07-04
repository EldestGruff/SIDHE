"""
Pydantic models for structured LLM outputs
Defines intent classification and entity extraction schemas

Architecture Decision: Uses Pydantic for type safety and validation
to ensure consistent structured outputs from LLM-based intent parsing.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
from enum import Enum

class IntentType(str, Enum):
    """Enumeration of supported intent types"""
    QUESTION = "question"
    MISSION_REQUEST = "mission_request"
    STATUS_CHECK = "status_check"
    COMMAND = "command"
    DISCUSSION = "discussion"
    TROUBLESHOOTING = "troubleshooting"

class ComplexityLevel(str, Enum):
    """Enumeration of request complexity levels"""
    SIMPLE = "simple"
    COMPLEX = "complex"
    MULTI_STEP = "multi_step"

class ConversationIntent(BaseModel):
    """Structured intent classification from user input"""
    type: IntentType = Field(description="The primary intent type")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for intent classification")
    
    # Entity extraction
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities from user input")
    
    # Plugin routing
    requires_plugins: List[str] = Field(default_factory=list, description="List of plugins needed to handle this intent")
    
    # Context requirements
    context_needed: List[str] = Field(default_factory=list, description="Types of context needed for processing")
    
    # Complexity assessment
    complexity: ComplexityLevel = Field(description="Complexity level of the request")
    
    # Additional metadata
    estimated_response_time: Optional[int] = Field(None, description="Estimated time to respond in seconds")
    requires_clarification: bool = Field(False, description="Whether the intent requires clarification")
    
    class Config:
        use_enum_values = True

class ConversationContext(BaseModel):
    """Context information for conversation processing"""
    conversation_id: str = Field(description="Unique conversation identifier")
    user_id: Optional[str] = Field(None, description="User identifier if available")
    session_id: str = Field(description="Session identifier")
    
    # Recent conversation history
    recent_turns: List[Dict[str, Any]] = Field(default_factory=list, description="Recent conversation turns")
    
    # Project context
    current_project: Optional[str] = Field(None, description="Current project context")
    active_missions: List[str] = Field(default_factory=list, description="List of active Away Mission IDs")
    
    # System state
    available_plugins: List[str] = Field(default_factory=list, description="List of available plugins")
    system_health: Dict[str, str] = Field(default_factory=dict, description="System health status")
    
    # User preferences
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences and settings")
    
    # Temporal context
    created_at: datetime = Field(default_factory=datetime.now, description="Context creation timestamp")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

class ConversationTurn(BaseModel):
    """Individual conversation turn data"""
    turn_id: str = Field(description="Unique turn identifier")
    conversation_id: str = Field(description="Parent conversation identifier")
    
    # Turn content
    user_input: str = Field(description="User input text")
    intent: ConversationIntent = Field(description="Parsed intent")
    system_response: Optional[str] = Field(None, description="System response")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Turn timestamp")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    
    # Plugin interactions
    plugin_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Plugin interactions made")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PluginMessage(BaseModel):
    """Message format for plugin communication"""
    plugin_id: str = Field(description="Target plugin identifier")
    action: str = Field(description="Action to perform")
    payload: Dict[str, Any] = Field(description="Message payload")
    
    # Routing information
    conversation_id: str = Field(description="Conversation context")
    turn_id: Optional[str] = Field(None, description="Turn context")
    
    # Message metadata
    message_id: str = Field(description="Unique message identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    timeout: int = Field(30, description="Message timeout in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PluginResponse(BaseModel):
    """Response format from plugin communication"""
    plugin_id: str = Field(description="Source plugin identifier")
    action: str = Field(description="Action that was performed")
    
    # Response data
    status: Literal["success", "error", "partial"] = Field(description="Response status")
    data: Dict[str, Any] = Field(description="Response data")
    error: Optional[str] = Field(None, description="Error message if status is error")
    
    # Metadata
    message_id: str = Field(description="Original message identifier")
    response_id: str = Field(description="Unique response identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    processing_time: float = Field(description="Processing time in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }