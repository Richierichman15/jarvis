"""
Dual Jarvis AI Assistant.
This extends the Jarvis class to use both local and OpenAI models in parallel.
"""
import logging
from typing import Dict, Any, Optional

from .jarvis import Jarvis
from .models.dual_model_manager import DualModelManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DualJarvis(Jarvis):
    """
    Dual Jarvis AI Assistant - Extension of Jarvis that runs both local and OpenAI models.
    This allows comparing the performance and quality of responses between models.
    """
    
    def __init__(self, user_name: str = "Boss"):
        """
        Initialize Dual Jarvis with all necessary components.
        
        Args:
            user_name: How Jarvis should address the user
        """
        # Call the parent constructor first
        super().__init__(user_name=user_name)
        
        # Replace the model manager with our dual model manager
        self.model_manager = DualModelManager()
        
        # Add system introduction to memory
        self._initialize_dual_system_messages()
    
    def _initialize_dual_system_messages(self):
        """Initialize system messages for the dual mode."""
        # Add system introduction to memory
        intro_message = (
            f"Hello {self.user_name}, I am JARVIS in dual-model mode. "
            "In this mode, I will show you responses from both the local and OpenAI models side by side, "
            "along with timing information so you can compare their performance. "
            "This allows you to see which model is faster and how their responses differ. "
            "How can I help you today?"
        )
        
        # Record the introduction in memory
        self.memory.add_message("assistant", intro_message)
    
    def process_query(self, query: str) -> str:
        """
        Process a user query and return responses from both models.
        
        Args:
            query: User's input query
            
        Returns:
            Combined response from both models with performance metrics
        """
        # Add user query to memory
        self.memory.add_message("user", query)
        
        # Check if we should use a tool
        tool_call = self._should_use_tool(query)
        tool_response = None
        
        if tool_call:
            tool_name = tool_call["tool"]
            params = tool_call["params"]
            
            # Execute the tool
            tool_response = self.tool_manager.execute_tool(tool_name, params)
            
            if tool_response:
                # Add tool response to memory
                self.memory.add_message(
                    "system", 
                    f"[Tool '{tool_name}' was used]",
                    {"tool_name": tool_name, "params": params}
                )
        
        # Prepare context for the model
        context = self._prepare_context()
        
        # Prepare the prompt based on tool response
        if tool_response and "web_search" in tool_response.lower():
            enhanced_system_prompt = (
                f"{self.system_prompt}\n\n"
                f"IMPORTANT: I've just performed a web search for the user. "
                f"The search results are below. "
                f"When formulating my response, I should use the information from these search results "
                f"to provide the most accurate and helpful information."
            )
            
            prompt = (
                f"The user asked: {query}\n\n"
                f"I performed a web search and found the following information:\n\n"
                f"{tool_response}\n\n"
                f"Based on these search results, please provide a helpful and accurate response to {self.user_name}, "
                f"citing sources where appropriate. Synthesize the information rather than just listing facts."
            )
            
            system_prompt = enhanced_system_prompt
        elif tool_response:
            prompt = (
                f"I used the {tool_call['tool']} tool to help answer the query: '{query}'. "
                f"Here is the information I found:\n\n{tool_response}\n\n"
                "Based on this information, please provide a helpful response to the user's query."
            )
            system_prompt = self.system_prompt
        else:
            prompt = (
                f"The user's query is: {query}\n\n"
                f"Conversation history:\n{context}\n\n"
                "Please provide a helpful response."
            )
            system_prompt = self.system_prompt
        
        # Get dual responses from both models
        response_data = self.model_manager.get_dual_response(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Extract the response text (combined from both models)
        response = response_data["response"]
        
        # Add assistant response to memory
        self.memory.add_message(
            "assistant", 
            response,
            {
                "model_used": "both",
                "complexity": response_data["complexity"],
                "local_time": response_data.get("local_time"),
                "openai_time": response_data.get("openai_time")
            }
        )
        
        return response
        
    def get_introduction(self) -> str:
        """
        Get Dual Jarvis's introduction message.
        
        Returns:
            Introduction message
        """
        messages = self.memory.get_conversation_history()
        for message in messages:
            if message["role"] == "assistant":
                return message["content"]
        
        # Fallback introduction
        return f"Hello {self.user_name}, I am JARVIS in dual-model mode. How can I assist you today?" 