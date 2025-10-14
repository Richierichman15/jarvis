"""
Jarvis Music Player - Discord voice client integration for music playback.
Connects Discord commands to the Music MCP Server.
"""

import asyncio
import discord
import logging
from typing import Optional, Dict, Any, List
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)


class MusicPlayer:
    """Handles music playback in Discord voice channels."""
    
    def __init__(self, jarvis_client):
        """
        Initialize the music player.
        
        Args:
            jarvis_client: JarvisClientMCPClient instance for MCP calls
        """
        self.jarvis_client = jarvis_client
        self.voice_clients: Dict[int, discord.VoiceClient] = {}  # guild_id -> voice_client
        self.current_song: Dict[int, Dict[str, Any]] = {}  # guild_id -> song info
        self.queue: Dict[int, deque] = {}  # guild_id -> song queue
        self.is_playing: Dict[int, bool] = {}  # guild_id -> playing status
        self.is_paused: Dict[int, bool] = {}  # guild_id -> paused status
    
    async def join_voice_channel(self, member: discord.Member, text_channel: discord.TextChannel) -> Optional[discord.VoiceClient]:
        """
        Join the voice channel of the member who invoked the command.
        
        Args:
            member: Discord member who invoked the command
            text_channel: Text channel to send messages to
            
        Returns:
            VoiceClient if successful, None otherwise
        """
        guild_id = member.guild.id
        
        # Check if member is in a voice channel
        if not member.voice or not member.voice.channel:
            await text_channel.send("❌ You need to be in a voice channel to use music commands!")
            return None
        
        voice_channel = member.voice.channel
        
        # If already connected to a voice channel in this guild
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_connected():
            # If in the same channel, just return it
            if self.voice_clients[guild_id].channel.id == voice_channel.id:
                return self.voice_clients[guild_id]
            else:
                # Move to the new channel
                await self.voice_clients[guild_id].move_to(voice_channel)
                logger.info(f"Moved to voice channel: {voice_channel.name}")
                return self.voice_clients[guild_id]
        
        # Connect to voice channel
        try:
            voice_client = await voice_channel.connect()
            self.voice_clients[guild_id] = voice_client
            logger.info(f"Connected to voice channel: {voice_channel.name} in {member.guild.name}")
            return voice_client
        except Exception as e:
            logger.error(f"Error connecting to voice channel: {e}")
            await text_channel.send(f"❌ Failed to connect to voice channel: {str(e)}")
            return None
    
    async def play_song(self, member: discord.Member, text_channel: discord.TextChannel, song_name: Optional[str] = None) -> str:
        """
        Play a song in the voice channel.
        
        Args:
            member: Discord member who invoked the command
            text_channel: Text channel to send messages to
            song_name: Optional song name to play
            
        Returns:
            Response message
        """
        guild_id = member.guild.id
        
        # Join voice channel if not already connected
        voice_client = await self.join_voice_channel(member, text_channel)
        if not voice_client:
            return "❌ Could not join voice channel"
        
        # If already playing, add to queue
        if guild_id in self.is_playing and self.is_playing[guild_id]:
            if song_name:
                # Add to queue
                if guild_id not in self.queue:
                    self.queue[guild_id] = deque()
                
                # Call MCP to get song info
                try:
                    result = await self.jarvis_client.call_tool(
                        "music.play_song",
                        {"song_name": song_name} if song_name else {},
                        "jarvis"
                    )
                    
                    # Parse result
                    song_info = self._parse_song_result(result)
                    if song_info:
                        self.queue[guild_id].append(song_info)
                        return f"➕ Added to queue: **{song_info['name']}** (Position {len(self.queue[guild_id])})"
                    else:
                        return "❌ Failed to get song information"
                except Exception as e:
                    logger.error(f"Error adding to queue: {e}")
                    return f"❌ Error: {str(e)}"
            else:
                return "⏯️ Already playing! Use `/queue <song_name>` to add songs to the queue."
        
        # Call Music MCP Server to get song
        try:
            logger.info(f"Requesting song from MCP: {song_name or 'random'}")
            
            result = await self.jarvis_client.call_tool(
                "music.play_song",
                {"song_name": song_name} if song_name else {},
                "jarvis"
            )
            
            # Parse the result to get song path and name
            song_info = self._parse_song_result(result)
            
            if not song_info:
                return "❌ Failed to get song information from Music MCP Server"
            
            # Play the audio
            await self._play_audio(guild_id, voice_client, song_info, text_channel)
            
            return f"🎶 Now playing: **{song_info['name']}**"
            
        except Exception as e:
            logger.error(f"Error playing song: {e}")
            return f"❌ Error: {str(e)}"
    
    def _parse_song_result(self, result: str) -> Optional[Dict[str, Any]]:
        """Parse the result from Music MCP Server."""
        import json
        
        try:
            # Try to parse as JSON
            if isinstance(result, str):
                # Look for JSON in the result
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    # Try parsing the whole string
                    data = json.loads(result)
            else:
                data = result
            
            # Extract song info
            if isinstance(data, dict):
                song_name = data.get('song_name') or data.get('name') or data.get('title')
                song_path = data.get('path') or data.get('file_path') or data.get('song_path')
                
                if song_name and song_path:
                    return {
                        'name': song_name,
                        'path': song_path,
                        'duration': data.get('duration'),
                        'artist': data.get('artist'),
                        'album': data.get('album')
                    }
            
            logger.warning(f"Could not parse song info from: {result}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing song result: {e}")
            return None
    
    async def _play_audio(self, guild_id: int, voice_client: discord.VoiceClient, song_info: Dict[str, Any], text_channel: discord.TextChannel):
        """Play audio file in voice channel."""
        try:
            song_path = song_info['path']
            
            # Verify file exists
            if not Path(song_path).exists():
                await text_channel.send(f"❌ Audio file not found: {song_path}")
                return
            
            # Create audio source
            audio_source = discord.FFmpegPCMAudio(song_path)
            
            # Store current song info
            self.current_song[guild_id] = song_info
            self.is_playing[guild_id] = True
            self.is_paused[guild_id] = False
            
            # Define what happens after song finishes
            def after_playing(error):
                if error:
                    logger.error(f"Error during playback: {error}")
                
                # Mark as not playing
                self.is_playing[guild_id] = False
                
                # Check if there's a queue
                if guild_id in self.queue and len(self.queue[guild_id]) > 0:
                    # Play next song in queue
                    next_song = self.queue[guild_id].popleft()
                    asyncio.run_coroutine_threadsafe(
                        self._play_next_in_queue(guild_id, voice_client, next_song, text_channel),
                        voice_client.loop
                    )
            
            # Play the audio
            voice_client.play(audio_source, after=after_playing)
            
            logger.info(f"Playing: {song_info['name']} in guild {guild_id}")
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            await text_channel.send(f"❌ Error playing audio: {str(e)}")
            self.is_playing[guild_id] = False
    
    async def _play_next_in_queue(self, guild_id: int, voice_client: discord.VoiceClient, song_info: Dict[str, Any], text_channel: discord.TextChannel):
        """Play the next song in the queue."""
        await text_channel.send(f"⏭️ Now playing from queue: **{song_info['name']}**")
        await self._play_audio(guild_id, voice_client, song_info, text_channel)
    
    async def pause(self, member: discord.Member, text_channel: discord.TextChannel) -> str:
        """Pause current playback."""
        guild_id = member.guild.id
        
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_connected():
            return "❌ Not connected to a voice channel"
        
        voice_client = self.voice_clients[guild_id]
        
        if not voice_client.is_playing():
            return "⏸️ Nothing is currently playing"
        
        if guild_id in self.is_paused and self.is_paused[guild_id]:
            return "⏸️ Already paused"
        
        voice_client.pause()
        self.is_paused[guild_id] = True
        
        current = self.current_song.get(guild_id, {})
        song_name = current.get('name', 'Unknown')
        
        return f"⏸️ Paused: **{song_name}**"
    
    async def resume(self, member: discord.Member, text_channel: discord.TextChannel) -> str:
        """Resume paused playback."""
        guild_id = member.guild.id
        
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_connected():
            return "❌ Not connected to a voice channel"
        
        voice_client = self.voice_clients[guild_id]
        
        if not voice_client.is_paused():
            return "▶️ Nothing is paused"
        
        voice_client.resume()
        self.is_paused[guild_id] = False
        
        current = self.current_song.get(guild_id, {})
        song_name = current.get('name', 'Unknown')
        
        return f"▶️ Resumed: **{song_name}**"
    
    async def stop(self, member: discord.Member, text_channel: discord.TextChannel) -> str:
        """Stop playback and clear queue."""
        guild_id = member.guild.id
        
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_connected():
            return "❌ Not connected to a voice channel"
        
        voice_client = self.voice_clients[guild_id]
        
        # Stop playback
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        
        # Clear queue
        if guild_id in self.queue:
            self.queue[guild_id].clear()
        
        # Clear state
        self.is_playing[guild_id] = False
        self.is_paused[guild_id] = False
        self.current_song.pop(guild_id, None)
        
        return "⏹️ Stopped playback and cleared queue"
    
    async def skip(self, member: discord.Member, text_channel: discord.TextChannel) -> str:
        """Skip to next song in queue."""
        guild_id = member.guild.id
        
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_connected():
            return "❌ Not connected to a voice channel"
        
        voice_client = self.voice_clients[guild_id]
        
        if not voice_client.is_playing():
            return "⏭️ Nothing is currently playing"
        
        # Check if there's a queue
        if guild_id not in self.queue or len(self.queue[guild_id]) == 0:
            voice_client.stop()
            return "⏭️ Skipped. No more songs in queue."
        
        # Stop current (after callback will play next)
        voice_client.stop()
        
        return "⏭️ Skipped to next song"
    
    async def add_to_queue(self, member: discord.Member, text_channel: discord.TextChannel, song_name: str) -> str:
        """Add a song to the queue."""
        guild_id = member.guild.id
        
        # Initialize queue if needed
        if guild_id not in self.queue:
            self.queue[guild_id] = deque()
        
        # Get song info from MCP
        try:
            result = await self.jarvis_client.call_tool(
                "music.play_song",
                {"song_name": song_name},
                "jarvis"
            )
            
            song_info = self._parse_song_result(result)
            
            if not song_info:
                return "❌ Could not find song"
            
            # Add to queue
            self.queue[guild_id].append(song_info)
            position = len(self.queue[guild_id])
            
            return f"➕ Added to queue: **{song_info['name']}** (Position {position})"
            
        except Exception as e:
            logger.error(f"Error adding to queue: {e}")
            return f"❌ Error: {str(e)}"
    
    async def show_queue(self, member: discord.Member, text_channel: discord.TextChannel) -> str:
        """Show the current queue."""
        guild_id = member.guild.id
        
        # Check current song
        current = self.current_song.get(guild_id)
        
        # Check queue
        queue = self.queue.get(guild_id, deque())
        
        if not current and len(queue) == 0:
            return "📜 Queue is empty"
        
        response = "🎵 **Music Queue**\n\n"
        
        # Current song
        if current:
            status = "⏸️ Paused" if self.is_paused.get(guild_id, False) else "▶️ Playing"
            response += f"{status} **{current['name']}**\n\n"
        
        # Queue
        if len(queue) > 0:
            response += "**Up Next:**\n"
            for i, song in enumerate(queue, 1):
                response += f"{i}. {song['name']}\n"
                if i >= 10:  # Limit to 10 songs
                    remaining = len(queue) - 10
                    if remaining > 0:
                        response += f"\n*...and {remaining} more*"
                    break
        else:
            if current:
                response += "*Queue is empty*"
        
        return response
    
    async def now_playing(self, member: discord.Member, text_channel: discord.TextChannel) -> str:
        """Show currently playing song."""
        guild_id = member.guild.id
        
        current = self.current_song.get(guild_id)
        
        if not current:
            return "🎵 Nothing is currently playing"
        
        status = "⏸️ Paused" if self.is_paused.get(guild_id, False) else "▶️ Playing"
        
        response = f"{status} **{current['name']}**"
        
        if current.get('artist'):
            response += f"\nArtist: {current['artist']}"
        
        if current.get('album'):
            response += f"\nAlbum: {current['album']}"
        
        if current.get('duration'):
            response += f"\nDuration: {current['duration']}"
        
        return response
    
    async def leave(self, member: discord.Member, text_channel: discord.TextChannel) -> str:
        """Leave voice channel."""
        guild_id = member.guild.id
        
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_connected():
            return "❌ Not in a voice channel"
        
        # Stop playback
        await self.stop(member, text_channel)
        
        # Disconnect
        await self.voice_clients[guild_id].disconnect()
        del self.voice_clients[guild_id]
        
        return "👋 Left voice channel"
    
    async def cleanup(self):
        """Cleanup all voice connections."""
        for guild_id, voice_client in self.voice_clients.items():
            try:
                if voice_client.is_connected():
                    await voice_client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from guild {guild_id}: {e}")
        
        self.voice_clients.clear()
        self.current_song.clear()
        self.queue.clear()
        self.is_playing.clear()
        self.is_paused.clear()
