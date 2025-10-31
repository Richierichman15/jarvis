"""Message utility functions for Discord bot."""
import asyncio
import logging
import aiohttp
from typing import List
from datetime import datetime
import discord

# Import config from discord_bot namespace
try:
    from discord_bot import config
except ImportError:
    # Fallback: try relative import if running as normal package
    try:
        from .. import config
    except ImportError:
        # Last resort: try importing discord_bot.config directly
        import sys
        if 'discord_bot.config' in sys.modules:
            import discord_bot.config as config
        else:
            raise ImportError("Could not import config module")

logger = logging.getLogger(__name__)


def split_message_intelligently(text: str, max_length: int = 1950) -> List[str]:
    """
    Split a long message into multiple parts at natural boundaries.
    
    Args:
        text: The text to split
        max_length: Maximum length per message (default 1950 to leave room for indicators)
        
    Returns:
        List of message chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by double newlines (paragraphs) first
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed limit
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            # If current chunk has content, save it
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # If paragraph itself is too long, split by sentences
            if len(paragraph) > max_length:
                sentences = paragraph.replace('. ', '.|').replace('! ', '!|').replace('? ', '?|').split('|')
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        
                        # If sentence itself is too long, split by character limit
                        if len(sentence) > max_length:
                            # Split at newlines within the long sentence
                            lines = sentence.split('\n')
                            for line in lines:
                                if len(current_chunk) + len(line) + 1 > max_length:
                                    if current_chunk:
                                        chunks.append(current_chunk.strip())
                                    current_chunk = line + '\n'
                                else:
                                    current_chunk += line + '\n'
                        else:
                            current_chunk = sentence + ' '
                    else:
                        current_chunk += sentence + ' '
            else:
                current_chunk = paragraph + '\n\n'
        else:
            current_chunk += paragraph + '\n\n'
    
    # Add any remaining content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


async def send_long_message(message: discord.Message, text: str) -> None:
    """
    Send a message that might be longer than Discord's 2000 character limit.
    Automatically splits into multiple messages with indicators.
    
    Args:
        message: The Discord message to reply to
        text: The text to send (can be any length)
    """
    chunks = split_message_intelligently(text, max_length=1950)
    
    if len(chunks) == 1:
        # Single message, send normally
        await message.reply(chunks[0])
        logger.info(f"Sent single message ({len(chunks[0])} chars)")
    else:
        # Multiple messages, add indicators
        logger.info(f"Splitting response into {len(chunks)} messages")
        
        for i, chunk in enumerate(chunks, 1):
            # Add message indicator
            indicator = f"📄 **Part {i}/{len(chunks)}**\n\n" if i > 1 else ""
            full_chunk = indicator + chunk
            
            # Send the chunk
            if i == 1:
                await message.reply(full_chunk)
            else:
                # For subsequent messages, send in the same channel
                await message.channel.send(full_chunk)
            
            # Small delay to ensure messages arrive in order
            if i < len(chunks):
                await asyncio.sleep(0.5)
        
        logger.info(f"Successfully sent {len(chunks)} message parts")


async def send_error_webhook(error_msg: str, original_message: str, session: aiohttp.ClientSession = None):
    """Send error notification to Discord webhook."""
    if not config.DISCORD_WEBHOOK_URL or not session:
        return
    
    try:
        webhook_data = {
            "content": f"🚨 **Jarvis Bot Error**\n\n**Error:** {error_msg}\n**Original Message:** {original_message}\n**Time:** {datetime.now().isoformat()}"
        }
        
        async with session.post(config.DISCORD_WEBHOOK_URL, json=webhook_data) as response:
            if response.status == 204:
                logger.info("Error notification sent to webhook")
            else:
                logger.error(f"Failed to send webhook: {response.status}")
                
    except Exception as e:
        logger.error(f"Error sending webhook: {e}")

