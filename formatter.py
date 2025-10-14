"""
Response Formatter for Jarvis Discord Bot
Transforms raw tool outputs (JSON/text) into natural, human-readable Discord messages.
"""

import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Formats raw tool outputs into natural, conversational responses using Jarvis AI."""
    
    def __init__(self, model_manager=None):
        """
        Initialize the formatter with an AI model.
        
        Args:
            model_manager: Jarvis model manager instance (OpenAI/Claude)
        """
        self.model_manager = model_manager
        
        # System prompt that defines Jarvis's formatting personality
        self.system_prompt = """You are Jarvis — a refined, intelligent AI assistant built for Discord.

Your task is to transform raw tool outputs into natural, conversational responses.

Input can be:
- JSON data (convert to natural language summary)
- Plain text (polish and improve readability)
- Error messages (make them clear and actionable)

Guidelines:
• If JSON → Parse and summarize key information in conversational tone
• If plain text → Polish for clarity while preserving all facts
• Use Discord markdown when helpful (**bold**, `code`, etc.)
• Keep responses concise but complete (2-5 sentences ideal)
• Tone: Confident, professional, slightly witty
• No added information beyond what's provided
• For numerical data, highlight key metrics
• For lists, present as bullet points when appropriate
• For errors, be clear about what went wrong

IMPORTANT: 
- Never say "based on the data" or "according to the output" - just present the information naturally
- Don't apologize or be uncertain - be confident
- Keep it brief unless the data is complex"""

    def is_json(self, text: str) -> bool:
        """Check if the text is valid JSON."""
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def clean_json_for_prompt(self, json_data: Any) -> str:
        """Convert JSON to a clean string format for the AI prompt."""
        try:
            # Pretty print the JSON for better readability
            return json.dumps(json_data, indent=2, sort_keys=False)
        except Exception:
            return str(json_data)
    
    def _determine_max_tokens(self, context: Optional[str], raw_response: str) -> int:
        """Determine appropriate token limit based on content type."""
        context_lower = (context or "").lower()
        
        # News scans and research need more space
        if any(word in context_lower for word in ['news', 'scan', 'research', 'search']):
            return 1000
        
        # Detailed queries need more space
        if any(word in context_lower for word in ['list', 'detail', 'explain', 'what are', 'top']):
            return 800
        
        # Complex data structures need more space
        if len(raw_response) > 2000:
            return 1200
        
        # If context says user expects detailed response
        if 'expects detailed response' in context_lower:
            return 1000
        
        # Default for simple queries
        return 500
    
    async def format_response(self, raw_response: str, context: Optional[str] = None) -> str:
        """
        Format a raw tool response into a natural, conversational message.
        
        Args:
            raw_response: The raw output from the tool (JSON or text)
            context: Optional context about what tool was called
            
        Returns:
            Formatted, human-readable response
        """
        # Handle empty responses
        if not raw_response or raw_response.strip() == "":
            return "I didn't receive any data back. The operation may have completed, but there's nothing to report."
        
        # Check if we have a model available
        if not self.model_manager:
            logger.warning("No model manager available, returning raw response")
            return raw_response
        
        try:
            # Determine response type
            is_json_response = self.is_json(raw_response)
            
            # Build the formatting prompt
            if is_json_response:
                json_data = json.loads(raw_response)
                clean_json = self.clean_json_for_prompt(json_data)
                
                prompt = f"""Transform this JSON data into a natural, conversational response:

```json
{clean_json}
```

Present the key information in a clear, confident way. Use Discord markdown for emphasis."""
                
            else:
                # Plain text response
                prompt = f"""Polish this response for Discord. Make it clear, confident, and well-formatted:

{raw_response}

Improve readability while keeping all facts intact. Use Discord markdown where helpful."""
            
            # Add context if provided
            if context:
                prompt = f"Context: {context}\n\n{prompt}"
            
            # Determine appropriate token limit based on content
            max_tokens = self._determine_max_tokens(context, raw_response)
            logger.info(f"Using {max_tokens} max tokens for response formatting")
            
            # Call the AI model to format the response
            formatted = self.model_manager.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            # Validate the formatted response
            if not formatted or "Error:" in formatted[:20]:
                logger.warning(f"Formatting failed: {formatted}")
                return self._fallback_format(raw_response, is_json_response)
            
            # Log successful formatting
            logger.info(f"Formatted response: {len(raw_response)} chars -> {len(formatted)} chars")
            
            return formatted.strip()
            
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return self._fallback_format(raw_response, is_json_response=self.is_json(raw_response))
    
    def _fallback_format(self, raw_response: str, is_json_response: bool) -> str:
        """
        Fallback formatting when AI model is unavailable.
        Simple rule-based formatting.
        """
        try:
            if is_json_response:
                data = json.loads(raw_response)
                
                # Handle common JSON structures
                if isinstance(data, dict):
                    # If it has an 'error' key, format as error
                    if 'error' in data:
                        return f"⚠️ Error: {data['error']}"
                    
                    # Format key-value pairs
                    lines = []
                    for key, value in data.items():
                        if isinstance(value, (dict, list)):
                            continue  # Skip complex nested structures
                        # Clean up key names (remove underscores, capitalize)
                        clean_key = key.replace('_', ' ').title()
                        lines.append(f"**{clean_key}:** {value}")
                    
                    if lines:
                        return "\n".join(lines[:10])  # Limit to 10 lines
                
                # For lists or other structures, just pretty print
                return f"```json\n{json.dumps(data, indent=2)[:1500]}\n```"
            
            else:
                # For plain text, just clean it up a bit
                lines = raw_response.strip().split('\n')
                # Remove excessive blank lines
                cleaned = '\n'.join(line for line in lines if line.strip())
                return cleaned[:1800]  # Limit length
                
        except Exception:
            # Last resort: return truncated raw response
            return raw_response[:1800]


# Singleton instance for easy import
_formatter_instance: Optional[ResponseFormatter] = None

def get_formatter(model_manager=None) -> ResponseFormatter:
    """
    Get or create the singleton ResponseFormatter instance.
    
    Args:
        model_manager: Model manager to use (only used on first call)
        
    Returns:
        ResponseFormatter instance
    """
    global _formatter_instance
    
    if _formatter_instance is None:
        _formatter_instance = ResponseFormatter(model_manager)
    elif model_manager is not None and _formatter_instance.model_manager is None:
        _formatter_instance.model_manager = model_manager
    
    return _formatter_instance


async def format_response(raw_response: str, model_manager=None, context: Optional[str] = None) -> str:
    """
    Convenience function to format a response.
    
    Args:
        raw_response: Raw tool output to format
        model_manager: Jarvis model manager (OpenAI/Claude)
        context: Optional context about the tool call
        
    Returns:
        Formatted, human-readable response
    """
    formatter = get_formatter(model_manager)
    return await formatter.format_response(raw_response, context)

