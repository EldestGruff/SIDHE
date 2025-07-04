"""
Intent Parser - LLM-based intent parsing with structured outputs
Implements intelligent conversation understanding using Anthropic's Claude API
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any
import anthropic
from .models import ConversationIntent, ConversationContext, IntentType, ComplexityLevel
from ..config.settings import settings

logger = logging.getLogger(__name__)

class IntentParser:
    """LLM-based intent parser using Anthropic Claude for structured outputs"""
    
    def __init__(self):
        """Initialize the Anthropic client"""
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        
        logger.info(f"IntentParser initialized with model: {self.model}")
    
    async def parse_intent(self, user_input: str, conversation_id: Optional[str] = None) -> ConversationIntent:
        """
        Parse user input into structured intent using Claude API
        
        Args:
            user_input: The user's input text
            conversation_id: Optional conversation ID for context
            
        Returns:
            ConversationIntent: Structured intent classification
        """
        try:
            # Build the intent parsing prompt
            prompt = self._build_intent_prompt(user_input)
            
            # Call Claude API for structured intent parsing
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=self.temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse the structured JSON response
            intent_data = json.loads(response.content[0].text)
            
            # Validate and create ConversationIntent object
            intent = ConversationIntent(**intent_data)
            
            logger.info(f"Parsed intent: {intent.type} (confidence: {intent.confidence})")
            return intent
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return self._fallback_intent(user_input)
        except Exception as e:
            logger.error(f"Intent parsing failed: {e}")
            return self._fallback_intent(user_input)
    
    def _build_intent_prompt(self, user_input: str) -> str:
        """Build the prompt for intent classification"""
        return f"""You are Riker's intent classification system. Parse the user input and return a JSON response with the intent classification.

Available intent types:
- question: General questions about the project, system, or how things work
- mission_request: Requests to create new features, fix bugs, or implement something
- status_check: Asking about current status of missions, system health, or progress
- command: Direct commands to perform specific actions
- discussion: Open-ended discussion about architecture, decisions, or planning
- troubleshooting: Help with debugging, errors, or issues

Available complexity levels:
- simple: Basic request that can be handled quickly
- complex: Multi-step request requiring planning
- multi_step: Complex workflow spanning multiple components

Available plugins that might be needed:
- github_integration: For creating missions, managing PRs, checking issues
- memory_manager: For remembering conversations and context
- config_manager: For configuration and settings management

User input: "{user_input}"

Respond with a JSON object matching this exact schema:
{{
    "type": "intent_type_from_list_above",
    "confidence": 0.85,
    "entities": {{"key": "extracted_entities_if_any"}},
    "requires_plugins": ["plugin_names_if_needed"],
    "context_needed": ["context_types_if_needed"],
    "complexity": "complexity_level_from_list_above",
    "estimated_response_time": 5,
    "requires_clarification": false
}}

Be specific about plugin requirements:
- If asking about missions/issues/PRs → require github_integration
- If asking about past conversations → require memory_manager  
- If asking about configuration → require config_manager
- If asking about multiple things → require multiple plugins

Analyze the complexity carefully:
- Simple: "What's the status of mission 3?" 
- Complex: "Help me plan an authentication system"
- Multi-step: "Build a complete REST API with auth, database, and testing"

Return only the JSON object, no other text."""

    def _fallback_intent(self, user_input: str) -> ConversationIntent:
        """Fallback intent when parsing fails"""
        logger.warning(f"Using fallback intent for: {user_input[:50]}...")
        
        # Simple heuristic-based classification as fallback
        lower_input = user_input.lower()
        
        if any(word in lower_input for word in ["status", "how is", "what's the", "show me"]):
            intent_type = IntentType.STATUS_CHECK
            plugins = ["github_integration"] if "mission" in lower_input else []
        elif any(word in lower_input for word in ["create", "build", "implement", "add", "make"]):
            intent_type = IntentType.MISSION_REQUEST
            plugins = ["github_integration"]
        elif any(word in lower_input for word in ["?", "how", "what", "why", "when"]):
            intent_type = IntentType.QUESTION
            plugins = []
        else:
            intent_type = IntentType.DISCUSSION
            plugins = []
        
        return ConversationIntent(
            type=intent_type,
            confidence=0.5,  # Low confidence for fallback
            entities={},
            requires_plugins=plugins,
            context_needed=[],
            complexity=ComplexityLevel.SIMPLE,
            estimated_response_time=10,
            requires_clarification=True
        )
