#!/usr/bin/env python3
"""
Jarvis Intelligence Core - Intent Router

This module provides intelligent command routing using LLM reasoning to interpret
natural language input and map it to the correct tools. It includes contextual
memory retrieval and detailed reasoning logs.

Features:
- LLM-based intent recognition
- Contextual memory retrieval
- Dynamic tool routing
- Reasoning logs
- Fallback mechanisms
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Import LLM capabilities
try:
    from brain.llm import generate as brain_generate
    BRAIN_AVAILABLE = True
except ImportError:
    BRAIN_AVAILABLE = False

try:
    from jarvis.models.model_manager import ModelManager
    MODEL_MANAGER_AVAILABLE = True
except ImportError:
    MODEL_MANAGER_AVAILABLE = False

# Import memory system
try:
    from brain import memory as brain_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

# Import conversation memory
try:
    from jarvis.memory.conversation_memory import ConversationMemory
    CONVERSATION_MEMORY_AVAILABLE = True
except ImportError:
    CONVERSATION_MEMORY_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Intent reasoning log file
INTENT_LOG_FILE = LOGS_DIR / "intents.log"


class IntentType(Enum):
    """Types of intents that can be recognized."""
    TRADING = "trading"
    MUSIC = "music"
    FITNESS = "fitness"
    NEWS = "news"
    SYSTEM = "system"
    SEARCH = "search"
    CHAT = "chat"
    UNKNOWN = "unknown"


@dataclass
class IntentContext:
    """Context information for intent processing."""
    user_id: str
    channel_id: str
    timestamp: datetime
    previous_intents: List[Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    system_state: Dict[str, Any]


@dataclass
class IntentResult:
    """Result of intent analysis."""
    intent_type: IntentType
    confidence: float
    tool_name: str
    arguments: Dict[str, Any]
    reasoning: str
    context_used: List[str]
    fallback_suggestions: List[str]
    processing_time: float


class ContextRetriever:
    """Retrieves contextual information for intent processing."""
    
    def __init__(self):
        self.conversation_memory = None
        self.brain_memory = None
        
        # Initialize conversation memory
        if CONVERSATION_MEMORY_AVAILABLE:
            try:
                self.conversation_memory = ConversationMemory()
                logger.info("✅ Conversation memory initialized")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize conversation memory: {e}")
        
        # Initialize brain memory
        if MEMORY_AVAILABLE:
            try:
                self.brain_memory = brain_memory
                logger.info("✅ Brain memory initialized")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize brain memory: {e}")
    
    async def get_user_context(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent user interactions for context."""
        context = []
        
        # Try conversation memory first
        if self.conversation_memory:
            try:
                recent_messages = await self.conversation_memory.get_recent_messages(
                    user_id, limit=limit
                )
                context.extend(recent_messages)
            except Exception as e:
                logger.warning(f"Error getting conversation memory: {e}")
        
        # Try brain memory as fallback
        if not context and self.brain_memory:
            try:
                # This would need to be implemented in brain memory
                # For now, we'll use a placeholder
                pass
            except Exception as e:
                logger.warning(f"Error getting brain memory: {e}")
        
        return context
    
    async def get_system_context(self) -> Dict[str, Any]:
        """Get current system state and context."""
        return {
            "timestamp": datetime.now().isoformat(),
            "available_tools": self._get_available_tools(),
            "system_status": "operational"
        }
    
    def _get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return [
            # Trading tools
            "trading.get_price", "trading.get_balance", "trading.get_portfolio",
            "trading.get_positions", "trading.get_trades", "trading.get_momentum_signals",
            "trading.get_pnl_summary", "trading.get_trade_history", "trading.doctor",
            
            # Music tools
            "music.play_song", "music.play_random", "music.search_songs",
            "music.list_songs", "music.add_to_queue", "music.get_queue",
            "music.pause", "music.resume", "music.stop", "music.skip",
            
            # Fitness tools
            "fitness.list_workouts", "fitness.search_workouts", "fitness.get_workout_plan",
            
            # News and search
            "jarvis_scan_news", "jarvis_web_search", "search.web.search",
            
            # System tools
            "jarvis_get_status", "jarvis_get_memory", "jarvis_get_tasks",
            "jarvis_chat", "system.system.list_quests", "system.system.get_status",
            
            # Event monitoring
            "events_start_monitoring", "events_stop_monitoring", "events_get_statistics"
        ]


class IntentRouter:
    """Main intent router that uses LLM reasoning to route commands."""
    
    def __init__(self):
        self.context_retriever = ContextRetriever()
        self.model_manager = None
        self.llm_available = False
        
        # Initialize LLM
        self._initialize_llm()
        
        # Tool mapping for fallback
        self.tool_mappings = self._build_tool_mappings()
        
        # Intent patterns for quick matching
        self.intent_patterns = self._build_intent_patterns()
        
        logger.info("🧠 IntentRouter initialized")
    
    def _initialize_llm(self):
        """Initialize the LLM for intent analysis."""
        if MODEL_MANAGER_AVAILABLE:
            try:
                self.model_manager = ModelManager()
                self.llm_available = True
                logger.info("✅ Model manager initialized for intent routing")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize model manager: {e}")
        
        if not self.llm_available and BRAIN_AVAILABLE:
            self.llm_available = True
            logger.info("✅ Brain LLM available for intent routing")
    
    def _build_tool_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Build comprehensive tool mappings for fallback routing."""
        return {
            # Trading mappings
            "portfolio": {"tool": "trading.portfolio.get_overview", "server": "jarvis"},
            "balance": {"tool": "trading.trading.get_balance", "server": "jarvis"},
            "positions": {"tool": "trading.portfolio.get_positions", "server": "jarvis"},
            "trades": {"tool": "trading.trading.get_recent_executions", "server": "jarvis"},
            "price": {"tool": "trading.trading.get_price", "server": "jarvis"},
            "momentum": {"tool": "trading.trading.get_momentum_signals", "server": "jarvis"},
            "pnl": {"tool": "trading.trading.get_pnl_summary", "server": "jarvis"},
            "doctor": {"tool": "trading.trading.doctor", "server": "jarvis"},
            
            # Music mappings
            "play": {"tool": "music_play", "server": "local"},
            "pause": {"tool": "music_pause", "server": "local"},
            "resume": {"tool": "music_resume", "server": "local"},
            "stop": {"tool": "music_stop", "server": "local"},
            "skip": {"tool": "music_skip", "server": "local"},
            "queue": {"tool": "music_queue_view", "server": "local"},
            "songs": {"tool": "music_list_songs", "server": "local"},
            
            # System mappings
            "status": {"tool": "jarvis_get_status", "server": "jarvis"},
            "memory": {"tool": "jarvis_get_memory", "server": "jarvis"},
            "tasks": {"tool": "jarvis_get_tasks", "server": "jarvis"},
            "quests": {"tool": "system.system.list_quests", "server": "jarvis"},
            "system": {"tool": "system.system.get_status", "server": "jarvis"},
            
            # News and search
            "news": {"tool": "jarvis_scan_news", "server": "jarvis"},
            "search": {"tool": "jarvis_web_search", "server": "jarvis"},
            
            # Events
            "events": {"tool": "events_get_statistics", "server": "local"},
        }
    
    def _build_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Build regex patterns for quick intent recognition."""
        return {
            IntentType.TRADING: [
                r'\b(portfolio|balance|positions|trades?|price|momentum|pnl|profit|loss|trading|invest|buy|sell)\b',
                r'\b(bitcoin|btc|ethereum|eth|crypto|stock|market|exchange)\b'
            ],
            IntentType.MUSIC: [
                r'\b(play|pause|resume|stop|skip|music|song|queue|volume|shuffle|random)\b',
                r'\b(join|leave|voice|channel|audio|sound)\b'
            ],
            IntentType.FITNESS: [
                r'\b(workout|exercise|fitness|gym|muscle|chest|back|legs|arms|cardio)\b',
                r'\b(push.?up|squat|deadlift|bench|press|curl|run|jog)\b'
            ],
            IntentType.NEWS: [
                r'\b(news|latest|recent|breaking|update|article|headline)\b',
                r'\b(ai|artificial intelligence|tech|technology|crypto|finance)\b'
            ],
            IntentType.SYSTEM: [
                r'\b(status|system|memory|tasks|quests|help|info|health)\b',
                r'\b(monitor|check|diagnose|debug|log)\b'
            ],
            IntentType.SEARCH: [
                r'\b(search|find|look.?up|google|web|internet|information)\b',
                r'\b(what|how|where|when|why|who)\b'
            ],
            IntentType.CHAT: [
                r'\b(hello|hi|hey|how.?are.?you|what.?up|good.?morning|good.?evening)\b',
                r'\b(thank.?you|thanks|please|sorry|help)\b'
            ]
        }
    
    async def analyze_intent(self, text: str, user_id: str, channel_id: str) -> IntentResult:
        """Analyze user input and determine the correct intent and tool."""
        start_time = time.time()
        
        try:
            # Get context
            context = await self._get_context(user_id, channel_id)
            
            # Try LLM-based analysis first
            if self.llm_available:
                result = await self._llm_intent_analysis(text, context)
                if result and result.confidence > 0.7:
                    processing_time = time.time() - start_time
                    result.processing_time = processing_time
                    await self._log_intent(text, result, context)
                    return result
            
            # Fallback to pattern matching
            result = await self._pattern_intent_analysis(text, context)
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            await self._log_intent(text, result, context)
            return result
            
        except Exception as e:
            logger.error(f"Error in intent analysis: {e}")
            # Return fallback result
            processing_time = time.time() - start_time
            return IntentResult(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                tool_name="jarvis_chat",
                arguments={"message": text},
                reasoning=f"Error in intent analysis: {str(e)}",
                context_used=[],
                fallback_suggestions=["Try rephrasing your request", "Use a specific command"],
                processing_time=processing_time
            )
    
    async def _get_context(self, user_id: str, channel_id: str) -> IntentContext:
        """Get comprehensive context for intent analysis."""
        # Get user conversation history
        conversation_history = await self.context_retriever.get_user_context(user_id)
        
        # Get system context
        system_context = await self.context_retriever.get_system_context()
        
        # Build previous intents from conversation history
        previous_intents = []
        for msg in conversation_history[-3:]:  # Last 3 interactions
            if msg.get('intent'):
                previous_intents.append(msg['intent'])
        
        return IntentContext(
            user_id=user_id,
            channel_id=channel_id,
            timestamp=datetime.now(),
            previous_intents=previous_intents,
            conversation_history=conversation_history,
            user_preferences={},  # Could be expanded
            system_state=system_context
        )
    
    async def _llm_intent_analysis(self, text: str, context: IntentContext) -> Optional[IntentResult]:
        """Use LLM to analyze intent and determine the correct tool."""
        try:
            # Build prompt for LLM
            prompt = self._build_intent_prompt(text, context)
            
            # Get LLM response
            if self.model_manager:
                response = await self.model_manager.generate_response(prompt)
            elif BRAIN_AVAILABLE:
                response = await brain_generate(prompt)
            else:
                return None
            
            # Parse LLM response
            return self._parse_llm_response(response, text)
            
        except Exception as e:
            logger.error(f"Error in LLM intent analysis: {e}")
            return None
    
    def _build_intent_prompt(self, text: str, context: IntentContext) -> str:
        """Build a comprehensive prompt for LLM intent analysis."""
        available_tools = context.system_state.get("available_tools", [])
        recent_history = context.conversation_history[-3:] if context.conversation_history else []
        
        prompt = f"""
You are Jarvis, an AI assistant with access to multiple tools. Analyze the user's request and determine the correct tool to use.

USER REQUEST: "{text}"

AVAILABLE TOOLS:
{json.dumps(available_tools, indent=2)}

RECENT CONVERSATION HISTORY:
{json.dumps(recent_history, indent=2)}

PREVIOUS INTENTS:
{json.dumps(context.previous_intents, indent=2)}

INSTRUCTIONS:
1. Determine the user's intent (trading, music, fitness, news, system, search, chat)
2. Select the most appropriate tool from the available tools
3. Extract any arguments needed for the tool
4. Provide confidence score (0.0-1.0)
5. Explain your reasoning

RESPONSE FORMAT (JSON):
{{
    "intent_type": "trading|music|fitness|news|system|search|chat",
    "confidence": 0.95,
    "tool_name": "trading.trading.get_balance",
    "arguments": {{}},
    "reasoning": "User is asking for portfolio balance, which maps to trading tool",
    "context_used": ["recent_trading_queries", "user_preferences"],
    "fallback_suggestions": ["Try /portfolio command", "Check /balance"]
}}

ANALYZE THE REQUEST:
"""
        return prompt
    
    def _parse_llm_response(self, response: str, original_text: str) -> Optional[IntentResult]:
        """Parse LLM response into IntentResult."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return None
            
            data = json.loads(json_match.group())
            
            return IntentResult(
                intent_type=IntentType(data.get("intent_type", "unknown")),
                confidence=float(data.get("confidence", 0.0)),
                tool_name=data.get("tool_name", "jarvis_chat"),
                arguments=data.get("arguments", {}),
                reasoning=data.get("reasoning", "LLM analysis"),
                context_used=data.get("context_used", []),
                fallback_suggestions=data.get("fallback_suggestions", []),
                processing_time=0.0  # Will be set by caller
            )
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return None
    
    async def _pattern_intent_analysis(self, text: str, context: IntentContext) -> IntentResult:
        """Fallback pattern-based intent analysis."""
        text_lower = text.lower()
        
        # Check each intent type
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Found a match, determine tool
                    tool_info = self._determine_tool_from_pattern(intent_type, text_lower)
                    
                    return IntentResult(
                        intent_type=intent_type,
                        confidence=0.6,  # Lower confidence for pattern matching
                        tool_name=tool_info["tool"],
                        arguments=tool_info.get("arguments", {}),
                        reasoning=f"Pattern matched for {intent_type.value}: {pattern}",
                        context_used=["pattern_matching"],
                        fallback_suggestions=["Try being more specific", "Use exact command syntax"],
                        processing_time=0.0
                    )
        
        # No pattern matched, default to chat
        return IntentResult(
            intent_type=IntentType.CHAT,
            confidence=0.3,
            tool_name="jarvis_chat",
            arguments={"message": text},
            reasoning="No specific intent pattern matched, defaulting to chat",
            context_used=["fallback"],
            fallback_suggestions=["Try using specific commands", "Ask for help"],
            processing_time=0.0
        )
    
    def _determine_tool_from_pattern(self, intent_type: IntentType, text: str) -> Dict[str, Any]:
        """Determine the specific tool based on intent type and text content."""
        if intent_type == IntentType.TRADING:
            if "portfolio" in text:
                return {"tool": "trading.portfolio.get_overview", "server": "jarvis"}
            elif "balance" in text:
                return {"tool": "trading.trading.get_balance", "server": "jarvis"}
            elif "price" in text:
                # Extract symbol if present
                symbol_match = re.search(r'\b([A-Z]{2,5})\b', text.upper())
                symbol = symbol_match.group(1) if symbol_match else "BTC"
                return {
                    "tool": "trading.trading.get_price",
                    "server": "jarvis",
                    "arguments": {"symbol": f"{symbol}/USD"}
                }
            elif "momentum" in text:
                return {"tool": "trading.trading.get_momentum_signals", "server": "jarvis"}
            elif "trades" in text:
                return {"tool": "trading.trading.get_recent_executions", "server": "jarvis"}
            else:
                return {"tool": "trading.portfolio.get_overview", "server": "jarvis"}
        
        elif intent_type == IntentType.MUSIC:
            if "play" in text:
                # Extract song name if present
                song_match = re.search(r'play\s+(.+)', text)
                if song_match:
                    return {
                        "tool": "music_play",
                        "server": "local",
                        "arguments": {"song_name": song_match.group(1).strip()}
                    }
                else:
                    return {"tool": "music_play_or_resume", "server": "local"}
            elif "pause" in text:
                return {"tool": "music_pause", "server": "local"}
            elif "resume" in text:
                return {"tool": "music_resume", "server": "local"}
            elif "stop" in text:
                return {"tool": "music_stop", "server": "local"}
            elif "skip" in text:
                return {"tool": "music_skip", "server": "local"}
            elif "queue" in text:
                return {"tool": "music_queue_view", "server": "local"}
            else:
                return {"tool": "music_play_or_resume", "server": "local"}
        
        elif intent_type == IntentType.FITNESS:
            if "chest" in text:
                return {
                    "tool": "fitness.list_workouts",
                    "server": "jarvis",
                    "arguments": {"muscle_group": "chest"}
                }
            elif "leg" in text:
                return {
                    "tool": "fitness.list_workouts",
                    "server": "jarvis",
                    "arguments": {"muscle_group": "legs"}
                }
            elif "back" in text:
                return {
                    "tool": "fitness.list_workouts",
                    "server": "jarvis",
                    "arguments": {"muscle_group": "back"}
                }
            else:
                return {"tool": "fitness.list_workouts", "server": "jarvis"}
        
        elif intent_type == IntentType.NEWS:
            return {"tool": "jarvis_scan_news", "server": "jarvis"}
        
        elif intent_type == IntentType.SYSTEM:
            if "status" in text:
                return {"tool": "jarvis_get_status", "server": "jarvis"}
            elif "memory" in text:
                return {"tool": "jarvis_get_memory", "server": "jarvis"}
            elif "tasks" in text:
                return {"tool": "jarvis_get_tasks", "server": "jarvis"}
            elif "quests" in text:
                return {"tool": "system.system.list_quests", "server": "jarvis"}
            else:
                return {"tool": "jarvis_get_status", "server": "jarvis"}
        
        elif intent_type == IntentType.SEARCH:
            # Extract search query
            query_match = re.search(r'search\s+(.+)', text)
            if query_match:
                return {
                    "tool": "jarvis_web_search",
                    "server": "jarvis",
                    "arguments": {"query": query_match.group(1).strip()}
                }
            else:
                return {"tool": "jarvis_web_search", "server": "jarvis"}
        
        else:
            return {"tool": "jarvis_chat", "server": "jarvis", "arguments": {"message": text}}
    
    async def _log_intent(self, text: str, result: IntentResult, context: IntentContext):
        """Log intent analysis results for debugging and improvement."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": context.user_id,
            "channel_id": context.channel_id,
            "input_text": text,
            "intent_result": asdict(result),
            "context_summary": {
                "conversation_length": len(context.conversation_history),
                "previous_intents": len(context.previous_intents),
                "system_status": context.system_state.get("system_status", "unknown")
            }
        }
        
        try:
            with open(INTENT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, indent=2) + "\n\n")
        except Exception as e:
            logger.error(f"Error logging intent: {e}")
    
    def get_intent_statistics(self) -> Dict[str, Any]:
        """Get statistics about intent analysis performance."""
        try:
            if not INTENT_LOG_FILE.exists():
                return {"error": "No intent logs found"}
            
            stats = {
                "total_requests": 0,
                "intent_types": {},
                "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
                "processing_times": [],
                "llm_vs_pattern": {"llm": 0, "pattern": 0}
            }
            
            with open(INTENT_LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                entries = content.split("\n\n")
                
                for entry in entries:
                    if entry.strip():
                        try:
                            data = json.loads(entry)
                            stats["total_requests"] += 1
                            
                            intent_type = data["intent_result"]["intent_type"]
                            stats["intent_types"][intent_type] = stats["intent_types"].get(intent_type, 0) + 1
                            
                            confidence = data["intent_result"]["confidence"]
                            if confidence >= 0.8:
                                stats["confidence_distribution"]["high"] += 1
                            elif confidence >= 0.5:
                                stats["confidence_distribution"]["medium"] += 1
                            else:
                                stats["confidence_distribution"]["low"] += 1
                            
                            processing_time = data["intent_result"]["processing_time"]
                            stats["processing_times"].append(processing_time)
                            
                            # Determine if LLM or pattern was used
                            reasoning = data["intent_result"]["reasoning"]
                            if "LLM" in reasoning or "brain" in reasoning.lower():
                                stats["llm_vs_pattern"]["llm"] += 1
                            else:
                                stats["llm_vs_pattern"]["pattern"] += 1
                                
                        except json.JSONDecodeError:
                            continue
            
            # Calculate average processing time
            if stats["processing_times"]:
                stats["average_processing_time"] = sum(stats["processing_times"]) / len(stats["processing_times"])
            
            return stats
            
        except Exception as e:
            return {"error": f"Error calculating statistics: {e}"}


# Global intent router instance
_intent_router = None


def get_intent_router() -> IntentRouter:
    """Get the global intent router instance."""
    global _intent_router
    if _intent_router is None:
        _intent_router = IntentRouter()
    return _intent_router


async def analyze_user_intent(text: str, user_id: str, channel_id: str) -> IntentResult:
    """Convenience function to analyze user intent."""
    router = get_intent_router()
    return await router.analyze_intent(text, user_id, channel_id)


if __name__ == "__main__":
    # Test the intent router
    async def test_intent_router():
        router = IntentRouter()
        
        test_cases = [
            "show me my portfolio balance",
            "play some music",
            "what's the price of Bitcoin?",
            "get me chest workouts",
            "scan the latest news",
            "how are you doing?",
            "search for AI developments"
        ]
        
        for text in test_cases:
            print(f"\n🔍 Testing: '{text}'")
            result = await router.analyze_intent(text, "test_user", "test_channel")
            print(f"Intent: {result.intent_type.value}")
            print(f"Tool: {result.tool_name}")
            print(f"Confidence: {result.confidence}")
            print(f"Reasoning: {result.reasoning}")
        
        # Show statistics
        stats = router.get_intent_statistics()
        print(f"\n📊 Statistics: {json.dumps(stats, indent=2)}")
    
    asyncio.run(test_intent_router())
