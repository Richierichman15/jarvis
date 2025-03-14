"""
Jarvis AI Assistant.
This is the main class that integrates all components together.
"""
import os
import time
import logging
from typing import Dict, Any, Optional, List

from .models.model_manager import ModelManager
from .memory.conversation_memory import ConversationMemory
from .tools.tool_manager import ToolManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Jarvis:
    """
    Jarvis AI Assistant - Your personal AI companion.
    Modeled after the AI from Iron Man, this assistant uses a hybrid approach
    with local and cloud AI models for intelligence.
    """
    
    def __init__(self, user_name: str = "Boss"):
        """
        Initialize Jarvis with all necessary components.
        
        Args:
            user_name: How Jarvis should address the user
        """
        self.user_name = user_name
        self.model_manager = ModelManager()
        self.memory = ConversationMemory()
        self.tool_manager = ToolManager()
        
        # Add system introduction to memory
        self._initialize_system_messages()
    
    def _initialize_system_messages(self):
        """Initialize system messages and introduction."""
        # Add system introduction to memory
        intro_message = (
            f"Hello {self.user_name}, I am JARVIS - Just A Rather Very Intelligent System. "
            "I'm here to assist you with various tasks, answer questions, and provide information. "
            "I can use tools like web search to find information for you, and I can remember our conversations. "
            "How can I help you today?"
        )
        
        # System message for model context
        self.system_prompt = (
            "You are JARVIS (Just A Rather Very Intelligent System), an advanced AI assistant inspired by "
            "the AI from Iron Man. Your responses should be helpful, informative, and concise. "
            f"Address the user as {self.user_name}. Use a friendly, slightly formal tone. "
            "If you don't know something, say so clearly rather than making up information. "
            "You have access to various tools that you can use to help answer questions."
        )
        
        # Record the introduction in memory
        self.memory.add_message("system", self.system_prompt)
        self.memory.add_message("assistant", intro_message)
    
    def _prepare_context(self) -> str:
        """
        Prepare context for the model based on conversation history.
        
        Returns:
            Context string to provide to the model
        """
        return self.memory.format_for_context()
    
    def _should_use_tool(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Determine if a tool should be used for the given query.
        
        Args:
            query: User's input query
            
        Returns:
            Tool call information or None
        """
        tool_calls = self.tool_manager.detect_tool_calls(query)
        if tool_calls:
            # For now, just use the first detected tool call
            return tool_calls[0]
        return None
        
    def process_query(self, query: str) -> str:
        """
        Process a user query and return a response.
        
        Args:
            query: User's input query
            
        Returns:
            Jarvis's response
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
        
        # If we have a tool response, let's create a more specific prompt
        if tool_response and "web_search" in tool_response.lower():
            enhanced_system_prompt = (
                f"{self.system_prompt}\n\n"
                f"IMPORTANT: I've just performed a web search for the user. "
                f"The search results are below. "
                f"When formulating my response, I should use the information from these search results "
                f"to provide the most accurate and helpful information. "
                f"I should NOT make up information or claim I don't have access to information "
                f"that is clearly available in the search results. "
                f"I should summarize the relevant information from the search results in a clear, "
                f"concise manner, citing the sources where appropriate."
            )
            
            # Check if we have news results in the response
            has_news = "NEWS RESULTS:" in tool_response
            has_images = "IMAGE DESCRIPTIONS:" in tool_response
            
            # Create a more specific prompt based on the type of search results
            if has_news:
                prompt = (
                    f"The user asked: {query}\n\n"
                    f"I performed a news search and found the following information:\n\n"
                    f"{tool_response}\n\n"
                    f"Based on these news results, please provide a summary of recent developments "
                    f"and relevant information to answer {self.user_name}'s query. Include source attribution "
                    f"where appropriate, and highlight the most recent and relevant information."
                )
            elif has_images:
                prompt = (
                    f"The user asked: {query}\n\n"
                    f"I performed a search that included image information and found the following:\n\n"
                    f"{tool_response}\n\n"
                    f"Based on these search results, please provide a helpful response to {self.user_name} "
                    f"that incorporates both textual information and descriptions of relevant images. "
                    f"Describe what the images show according to their descriptions."
                )
            else:
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
        
        # Get response from the model
        response_data = self.model_manager.get_response(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Extract the response text
        response = response_data["response"]
        
        # Add assistant response to memory
        self.memory.add_message(
            "assistant", 
            response,
            {"model_used": response_data["model_used"], "complexity": response_data["complexity"]}
        )
        
        return response
        
    def get_introduction(self) -> str:
        """
        Get Jarvis's introduction message.
        
        Returns:
            Introduction message
        """
        messages = self.memory.get_conversation_history()
        for message in messages:
            if message["role"] == "assistant":
                return message["content"]
        
        # Fallback introduction
        return f"Hello {self.user_name}, I am JARVIS. How can I assist you today?" 