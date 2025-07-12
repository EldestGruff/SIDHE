"""
AI Conversation Handler - True AI conversation capability for SIDHE
Provides intelligent conversational AI using Anthropic's Claude API
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
import anthropic
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)

class AIConversationHandler:
    """Advanced AI conversation handler using Claude for intelligent responses"""
    
    def __init__(self):
        """Initialize the Anthropic client"""
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model
        self.temperature = 0.7  # More creative for conversations
        
        # SIDHE persona and capabilities
        self.system_prompt = """You are SIDHE, an Ancient AI Development Companion with mystical wisdom and modern technical expertise. You embody the spirit of the legendary Sidhe - powerful, wise beings from Celtic mythology who possessed deep knowledge of the natural and supernatural worlds.

Your Capabilities:
- Full-stack software development assistance (Python, JavaScript, React, FastAPI, databases, etc.)
- Code review, debugging, and optimization
- Architecture design and technical decision-making
- Project planning and management
- DevOps, deployment, and infrastructure guidance
- Best practices and security recommendations
- Creative problem-solving with both ancient wisdom and cutting-edge technology

Your Personality:
- Wise and knowledgeable, drawing from both ancient wisdom and modern expertise
- Helpful and supportive, always seeking to empower developers
- Mystical yet practical - you can discuss abstract concepts and concrete implementations
- Patient teacher who explains complex topics clearly
- Encouraging and positive, helping developers grow their skills

Response Style:
- Be conversational and engaging
- Provide detailed, actionable advice when asked technical questions
- Use occasional mystical references naturally (but don't overdo it)
- Be concise when appropriate, detailed when needed
- Always aim to be helpful and constructive
- Include code examples when relevant
- Ask clarifying questions when needed

You are part of a larger system with plugins for GitHub integration, memory management, and configuration management. When users ask about specific project tasks, quest tracking, or system status, acknowledge that you can coordinate with these systems, but your primary role is as an intelligent conversational AI assistant.

Current date: {current_date}"""
        
        logger.info(f"AIConversationHandler initialized with model: {self.model}")
    
    async def generate_response(self, user_input: str, conversation_history: Optional[List[Dict]] = None, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate an intelligent AI response using Claude
        
        Args:
            user_input: The user's message
            conversation_history: Previous messages in the conversation
            context: Additional context (intent, metadata, etc.)
            
        Returns:
            Dict containing the AI response and metadata
        """
        try:
            # Build conversation messages
            messages = self._build_conversation_messages(user_input, conversation_history, context)
            
            # Generate response using Claude
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=self.temperature,
                system=self.system_prompt.format(current_date=datetime.now().strftime("%Y-%m-%d")),
                messages=messages
            )
            
            ai_response = response.content[0].text
            
            # Return structured response
            return {
                "type": "assistant_response",
                "content": ai_response,
                "model": self.model,
                "timestamp": datetime.now().isoformat(),
                "token_count": response.usage.output_tokens if hasattr(response, 'usage') else None,
                "context": context
            }
            
        except Exception as e:
            logger.error(f"AI conversation generation failed: {e}")
            return {
                "type": "error",
                "content": "I encountered an issue while processing your message. My ancient wisdom seems temporarily clouded. Please try again.",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_conversation_messages(self, user_input: str, conversation_history: Optional[List[Dict]], context: Optional[Dict]) -> List[Dict]:
        """Build the message list for Claude API"""
        messages = []
        
        # Add conversation history if available (keep last 10 messages)
        if conversation_history:
            history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
            for msg in history:
                if msg.get('sender') == 'user':
                    messages.append({
                        "role": "user",
                        "content": msg.get('content', '')
                    })
                elif msg.get('sender') == 'assistant':
                    messages.append({
                        "role": "assistant", 
                        "content": msg.get('content', '')
                    })
        
        # Add context information if provided
        context_info = ""
        if context:
            if context.get('intent'):
                context_info += f"\nUser intent detected: {context['intent']}"
            if context.get('confidence'):
                context_info += f" (confidence: {context['confidence']:.2f})"
            if context.get('entities'):
                context_info += f"\nEntities: {context['entities']}"
        
        # Add current user message
        current_message = user_input
        if context_info:
            current_message += f"\n\n[System Context: {context_info.strip()}]"
        
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        return messages
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the AI handler is working correctly"""
        try:
            # Simple test call to verify API connectivity
            test_response = await self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[{
                    "role": "user",
                    "content": "Respond with just 'SIDHE AI ready' to confirm you're working."
                }]
            )
            
            return {
                "status": "healthy",
                "model": self.model,
                "test_response": test_response.content[0].text,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }