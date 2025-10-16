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
                        "play_song",
                        {"song_name": song_name} if song_name else {},
                        "music"
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
                "play_song",
                {"song_name": song_name} if song_name else {},
                "music"
            )
            
            # Parse the result to get song path and name
            logger.info(f"Raw MCP result: {result}")
            song_info = self._parse_song_result(result)
            
            # If exact match failed and song_name was provided, try searching
            if not song_info and song_name:
                logger.info(f"Exact match failed, searching for: {song_name}")
                try:
                    search_result = await self.jarvis_client.call_tool(
                        "search_song",
                        {"keyword": song_name},
                        "music"
                    )
                    
                    # Parse search results
                    song_info = self._parse_search_result(search_result)
                    
                    if song_info:
                        logger.info(f"Found song via search: {song_info['name']}")
                    else:
                        # List available songs for user
                        return await self._suggest_songs(song_name)
                        
                except Exception as e:
                    logger.error(f"Search failed: {e}")
                    return await self._suggest_songs(song_name)
            
            if not song_info:
                return await self._suggest_songs(song_name)
            
            # Play the audio (this will send message directly to channel)
            success = await self._play_audio(guild_id, voice_client, song_info, text_channel)
            
            logger.info(f"_play_audio returned: {success}")
            
            if success:
                # Auto-queue 5 random songs if queue is empty
                if guild_id not in self.queue or len(self.queue[guild_id]) == 0:
                    logger.info("Auto-queuing 5 random songs...")
                    asyncio.create_task(self.play_random(member, text_channel, count=5, auto_queue=True))
                
                return f"🎶 Now playing: **{song_info['name']}**"
            else:
                return f"❌ Failed to play: **{song_info['name']}**"
            
        except Exception as e:
            logger.error(f"Error playing song: {e}")
            return f"❌ Error: {str(e)}"
    
    def _parse_song_result(self, result: str) -> Optional[Dict[str, Any]]:
        """Parse the result from Music MCP Server."""
        import json
        
        try:
            logger.info(f"Parsing song result, type: {type(result)}, value: {result}")
            
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
            
            logger.info(f"Parsed data: {data}")
            
            # Check if there's an error
            if isinstance(data, dict) and data.get('error'):
                logger.warning(f"Music server returned error: {data.get('error')}")
                return None
            
            # Extract song info
            if isinstance(data, dict):
                song_name = data.get('song_name') or data.get('song') or data.get('name') or data.get('title')
                song_path = data.get('path') or data.get('file_path') or data.get('song_path')
                
                logger.info(f"Extracted - song_name: {song_name}, song_path: {song_path}")
                
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
            logger.exception(e)
            return None
    
    def _parse_search_result(self, result: str) -> Optional[Dict[str, Any]]:
        """Parse search results and return the first match."""
        import json
        
        try:
            if isinstance(result, str):
                data = json.loads(result)
            else:
                data = result
            
            # Check if it's a list of results
            if isinstance(data, list) and len(data) > 0:
                # Return first match
                first_match = data[0]
                return {
                    'name': first_match.get('name') or first_match.get('title'),
                    'path': first_match.get('path'),
                    'duration': first_match.get('duration'),
                    'artist': first_match.get('artist'),
                    'album': first_match.get('album')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing search result: {e}")
            return None
    
    async def _suggest_songs(self, failed_query: Optional[str] = None) -> str:
        """List available songs when song not found, with fuzzy matching."""
        try:
            # Get list of available songs
            result = await self.jarvis_client.call_tool(
                "list_songs",
                {},
                "music"
            )
            
            import json
            if isinstance(result, str):
                data = json.loads(result)
            else:
                data = result
            
            if isinstance(data, list) and len(data) > 0:
                # If we have a query, try to find partial matches
                partial_matches = []
                if failed_query:
                    query_lower = failed_query.lower()
                    query_words = query_lower.split()
                    
                    for song in data:
                        song_name = song.get('name', '').lower()
                        song_title = song.get('title', '').lower()
                        
                        # Check if any query word is in the song name
                        if any(word in song_name or word in song_title for word in query_words):
                            partial_matches.append(song.get('name', 'Unknown'))
                
                response = f"❌ Song not found: **{failed_query}**\n\n"
                
                # Show partial matches first
                if partial_matches:
                    response += f"🔍 **Did you mean:**\n"
                    for i, match in enumerate(partial_matches[:5], 1):
                        response += f"{i}. {match}\n"
                    response += f"\n"
                
                # Show some random songs as suggestions
                import random
                random_songs = random.sample(data, min(5, len(data)))
                response += f"📀 **Or try these:**\n"
                for song in random_songs:
                    response += f"• {song.get('name', 'Unknown')}\n"
                
                response += f"\n💡 Use `/songs` to see all {len(data)} songs"
                response += f"\n💡 Use `/findsong <keyword>` to search"
                
                return response
            else:
                return "❌ Song not found and could not retrieve song list"
                
        except Exception as e:
            logger.error(f"Error suggesting songs: {e}")
            return f"❌ Song not found: {failed_query or 'unknown'}"
    
    async def _play_audio(self, guild_id: int, voice_client: discord.VoiceClient, song_info: Dict[str, Any], text_channel: discord.TextChannel) -> bool:
        """Play audio file in voice channel. Returns True if successful, False otherwise."""
        try:
            song_path = song_info['path']
            
            logger.info(f"Checking if file exists: {song_path}")
            logger.info(f"Path object: {Path(song_path)}")
            logger.info(f"Path exists: {Path(song_path).exists()}")
            logger.info(f"Path is_file: {Path(song_path).is_file()}")
            
            # Verify file exists
            if not Path(song_path).exists():
                await text_channel.send(f"❌ Audio file not found: {song_path}")
                logger.error(f"File not found at: {song_path}")
                return False
            
            # Create audio source
            try:
                logger.info(f"Creating FFmpegPCMAudio for: {song_path}")
                audio_source = discord.FFmpegPCMAudio(song_path)
                logger.info(f"FFmpegPCMAudio created successfully")
            except Exception as ffmpeg_error:
                error_msg = str(ffmpeg_error)
                logger.error(f"FFmpeg error: {error_msg}")
                if "ffmpeg was not found" in error_msg or "ffmpeg" in error_msg.lower():
                    await text_channel.send(
                        "❌ **FFmpeg not found!**\n"
                        "Please restart your Discord bot (close PowerShell and start again) "
                        "so it picks up the newly installed FFmpeg."
                    )
                else:
                    await text_channel.send(f"❌ Audio error: {error_msg}")
                return False
            
            # Store current song info
            self.current_song[guild_id] = song_info
            self.is_playing[guild_id] = True
            self.is_paused[guild_id] = False
            
            logger.info(f"About to play audio in voice client")
            
            # Define what happens after song finishes
            def after_playing(error):
                if error:
                    logger.error(f"Error during playback: {error}")
                else:
                    logger.info(f"Song finished playing: {song_info['name']}")
                
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
                else:
                    # Queue is empty - try to auto-queue 5 more songs before disconnecting
                    logger.info(f"Queue empty for guild {guild_id}, attempting to auto-queue...")
                    
                    # Get a member from voice channel for auto-queue
                    if voice_client and voice_client.channel:
                        members = [m for m in voice_client.channel.members if not m.bot]
                        if members:
                            logger.info("Auto-queuing 5 songs since queue is empty")
                            asyncio.run_coroutine_threadsafe(
                                self._auto_queue_on_empty(guild_id, voice_client, members[0], text_channel),
                                voice_client.loop
                            )
                        else:
                            # No members, disconnect after delay
                            asyncio.run_coroutine_threadsafe(
                                self._auto_disconnect_if_idle(guild_id, voice_client, 60),
                                voice_client.loop
                            )
                    else:
                        # Can't auto-queue, disconnect after delay
                        asyncio.run_coroutine_threadsafe(
                            self._auto_disconnect_if_idle(guild_id, voice_client, 60),
                            voice_client.loop
                        )
            
            # Play the audio
            logger.info(f"Calling voice_client.play()")
            voice_client.play(audio_source, after=after_playing)
            logger.info(f"voice_client.play() called successfully")
            
            logger.info(f"Playing: {song_info['name']} in guild {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            await text_channel.send(f"❌ Error playing audio: {str(e)}")
            self.is_playing[guild_id] = False
            return False
    
    async def _play_next_in_queue(self, guild_id: int, voice_client: discord.VoiceClient, song_info: Dict[str, Any], text_channel: discord.TextChannel):
        """Play the next song in the queue."""
        await text_channel.send(f"⏭️ Now playing from queue: **{song_info['name']}**")
        
        # Check if queue is running low (2 or fewer songs left)
        queue_length = len(self.queue.get(guild_id, deque()))
        if queue_length <= 2:
            logger.info(f"Queue running low ({queue_length} songs), auto-queuing 5 more...")
            # Get member from voice channel to pass to play_random
            if voice_client and voice_client.channel:
                # Find a member in the voice channel (any member will do for auto-queue)
                members = [m for m in voice_client.channel.members if not m.bot]
                if members:
                    asyncio.create_task(self.play_random(members[0], text_channel, count=5, auto_queue=True))
                    await text_channel.send("🎲 *Auto-queuing 5 more random songs...*")
        
        await self._play_audio(guild_id, voice_client, song_info, text_channel)
    
    async def _auto_queue_on_empty(self, guild_id: int, voice_client: discord.VoiceClient, member: discord.Member, text_channel: discord.TextChannel):
        """Auto-queue 5 songs when queue becomes empty, then play the first one."""
        try:
            await text_channel.send("🎲 *Queue empty! Auto-queuing 5 random songs...*")
            
            # Queue 5 random songs
            result = await self.play_random(member, text_channel, count=5, auto_queue=True)
            
            # Check if we successfully queued songs
            if guild_id in self.queue and len(self.queue[guild_id]) > 0:
                # Play the first queued song
                next_song = self.queue[guild_id].popleft()
                await self._play_next_in_queue(guild_id, voice_client, next_song, text_channel)
            else:
                # Failed to queue, disconnect after delay
                logger.warning("Failed to auto-queue songs, will disconnect")
                await text_channel.send("⚠️ *No more songs available. Disconnecting in 60 seconds...*")
                await self._auto_disconnect_if_idle(guild_id, voice_client, 60)
                
        except Exception as e:
            logger.error(f"Error auto-queuing on empty: {e}")
            await self._auto_disconnect_if_idle(guild_id, voice_client, 60)
    
    async def _auto_disconnect_if_idle(self, guild_id: int, voice_client: discord.VoiceClient, delay: int):
        """Disconnect from voice channel after delay if still idle."""
        await asyncio.sleep(delay)
        
        # Check if still idle (not playing and queue is empty)
        if (guild_id not in self.is_playing or not self.is_playing[guild_id]) and \
           (guild_id not in self.queue or len(self.queue[guild_id]) == 0):
            logger.info(f"Auto-disconnecting from guild {guild_id} due to inactivity")
            try:
                if voice_client.is_connected():
                    await voice_client.disconnect()
                    if guild_id in self.voice_clients:
                        del self.voice_clients[guild_id]
            except Exception as e:
                logger.error(f"Error auto-disconnecting: {e}")
    
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
        
        if not voice_client.is_playing() and not voice_client.is_paused():
            return "⏭️ Nothing is currently playing"
        
        # Get queue info before stopping
        queue_length = len(self.queue.get(guild_id, deque()))
        
        # Stop current (after callback will play next)
        voice_client.stop()
        
        if queue_length > 0:
            return f"⏭️ Skipped! Playing next song... ({queue_length} left in queue)"
        else:
            return "⏭️ Skipped. No more songs in queue."
    
    async def add_to_queue(self, member: discord.Member, text_channel: discord.TextChannel, song_name: str) -> str:
        """Add a song to the queue using MCP queue management."""
        guild_id = member.guild.id
        
        # Initialize queue if needed
        if guild_id not in self.queue:
            self.queue[guild_id] = deque()
        
        # Use MCP add_to_queue tool
        try:
            result = await self.jarvis_client.call_tool(
                "add_to_queue",
                {"song_name": song_name},
                "music"
            )
            
            import json
            if isinstance(result, str):
                data = json.loads(result)
            else:
                data = result
            
            if data.get('success'):
                # Also add to local queue for playback
                song_info = {
                    'name': data.get('song'),
                    'path': None  # Will get path when playing
                }
                
                # Get full song info for playback
                song_result = await self.jarvis_client.call_tool(
                    "play_song",
                    {"song_name": song_name},
                    "music"
                )
                full_song_info = self._parse_song_result(song_result)
                
                if full_song_info:
                    self.queue[guild_id].append(full_song_info)
                    position = len(self.queue[guild_id])
                    return f"➕ Added to queue: **{data.get('song')}** (Position {position})"
                else:
                    return f"➕ Added to MCP queue: **{data.get('song')}**"
            else:
                error = data.get('error', 'Unknown error')
                return f"❌ {error}"
            
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
    
    async def list_available_songs(self) -> str:
        """List all available songs."""
        try:
            result = await self.jarvis_client.call_tool(
                "list_songs",
                {},
                "music"
            )
            
            import json
            if isinstance(result, str):
                data = json.loads(result)
            else:
                data = result
            
            if isinstance(data, list) and len(data) > 0:
                # Group songs in batches of 15 for better readability
                song_list = []
                for i, song in enumerate(data[:20], 1):  # Limit to 20 to avoid message limits
                    song_name = song.get('name') or song.get('title', 'Unknown')
                    song_list.append(f"{i}. {song_name}")
                
                response = f"📀 **Available Songs** ({len(data)} total)\n\n"
                response += "\n".join(song_list)
                
                if len(data) > 20:
                    response += f"\n\n*...and {len(data) - 20} more songs*"
                
                response += f"\n\nUse `/play <song_name>` to play a song"
                
                return response
            else:
                return "📀 No songs available in the music library"
                
        except Exception as e:
            logger.error(f"Error listing songs: {e}")
            return f"❌ Error retrieving song list: {str(e)}"
    
    async def play_random(self, member: discord.Member, text_channel: discord.TextChannel, count: int = 1, auto_queue: bool = False) -> str:
        """Add random song(s) to the queue (or play if nothing is playing)."""
        guild_id = member.guild.id
        added_songs = []
        
        try:
            for i in range(count):
                result = await self.jarvis_client.call_tool(
                    "play_random",
                    {},
                    "music"
                )
                
                import json
                if isinstance(result, str):
                    data = json.loads(result)
                else:
                    data = result
                
                if data.get('error'):
                    logger.warning(f"Error getting random song: {data.get('error')}")
                    continue
                
                song_info = {
                    'name': data.get('song'),
                    'path': data.get('path'),
                    'duration': data.get('duration'),
                    'artist': data.get('artist'),
                    'album': data.get('album')
                }
                
                # If this is the first song and nothing is playing, play it
                if i == 0 and (guild_id not in self.is_playing or not self.is_playing[guild_id]):
                    voice_client = await self.join_voice_channel(member, text_channel)
                    
                    if not voice_client:
                        return "❌ Could not join voice channel"
                    
                    success = await self._play_audio(guild_id, voice_client, song_info, text_channel)
                    
                    if success:
                        added_songs.append(song_info['name'])
                    else:
                        logger.warning(f"Failed to play: {song_info['name']}")
                else:
                    # Add to queue
                    if guild_id not in self.queue:
                        self.queue[guild_id] = deque()
                    
                    self.queue[guild_id].append(song_info)
                    added_songs.append(song_info['name'])
            
            if not added_songs:
                return "❌ Failed to queue random songs"
            
            if auto_queue:
                # Silent auto-queue, don't send message
                return None
            
            if len(added_songs) == 1:
                if guild_id in self.is_playing and self.is_playing[guild_id]:
                    return f"🎲 Added random to queue: **{added_songs[0]}**"
                else:
                    return f"🎲 Playing random: **{added_songs[0]}**"
            else:
                return f"🎲 Queued {len(added_songs)} random songs!"
                
        except Exception as e:
            logger.error(f"Error playing random song: {e}")
            return f"❌ Error: {str(e)}"
    
    async def search_songs(self, keyword: str) -> str:
        """Search for songs matching a keyword."""
        try:
            result = await self.jarvis_client.call_tool(
                "search_song",
                {"keyword": keyword},
                "music"
            )
            
            import json
            if isinstance(result, str):
                data = json.loads(result)
            else:
                data = result
            
            if isinstance(data, list) and len(data) > 0:
                # Check if it's an error response
                if data[0].get('message'):
                    return f"🔍 {data[0]['message']}"
                
                # Format search results
                response = f"🔍 **Search results for:** `{keyword}`\n\n"
                for i, song in enumerate(data, 1):
                    song_name = song.get('name') or song.get('title', 'Unknown')
                    response += f"{i}. {song_name}\n"
                
                response += f"\nUse `/play <song_name>` to play"
                return response
            else:
                return f"🔍 No songs found matching: `{keyword}`"
                
        except Exception as e:
            logger.error(f"Error searching songs: {e}")
            return f"❌ Error: {str(e)}"
    
    async def clear_queue(self, member: discord.Member, text_channel: discord.TextChannel) -> str:
        """Clear the music queue."""
        guild_id = member.guild.id
        
        try:
            # Clear MCP queue
            result = await self.jarvis_client.call_tool(
                "clear_queue",
                {},
                "music"
            )
            
            # Clear local queue
            if guild_id in self.queue:
                cleared_count = len(self.queue[guild_id])
                self.queue[guild_id].clear()
            else:
                cleared_count = 0
            
            return f"🗑️ Cleared {cleared_count} song(s) from queue"
            
        except Exception as e:
            logger.error(f"Error clearing queue: {e}")
            return f"❌ Error: {str(e)}"
    
    async def remove_from_queue(self, member: discord.Member, text_channel: discord.TextChannel, position: int) -> str:
        """Remove a song from the queue by position."""
        guild_id = member.guild.id
        
        if guild_id not in self.queue or len(self.queue[guild_id]) == 0:
            return "❌ Queue is empty"
        
        # Convert to 0-based index
        index = position - 1
        
        if index < 0 or index >= len(self.queue[guild_id]):
            return f"❌ Invalid position. Queue has {len(self.queue[guild_id])} song(s)"
        
        try:
            # Remove from MCP queue
            result = await self.jarvis_client.call_tool(
                "remove_from_queue",
                {"index": index},
                "music"
            )
            
            # Remove from local queue
            queue_list = list(self.queue[guild_id])
            removed_song = queue_list.pop(index)
            self.queue[guild_id] = deque(queue_list)
            
            return f"🗑️ Removed from queue: **{removed_song['name']}**"
            
        except Exception as e:
            logger.error(f"Error removing from queue: {e}")
            return f"❌ Error: {str(e)}"
    
    async def get_mcp_queue(self) -> str:
        """Get the MCP server's queue status."""
        try:
            result = await self.jarvis_client.call_tool(
                "get_queue",
                {},
                "music"
            )
            
            import json
            if isinstance(result, str):
                data = json.loads(result)
            else:
                data = result
            
            queue_length = data.get('length', 0)
            queue_items = data.get('queue', [])
            
            if queue_length == 0:
                return "📜 MCP Queue is empty"
            
            response = f"📜 **MCP Queue** ({queue_length} songs)\n\n"
            for i, song in enumerate(queue_items[:10], 1):
                song_name = song.get('name') or song.get('title', 'Unknown')
                response += f"{i}. {song_name}\n"
            
            if queue_length > 10:
                response += f"\n*...and {queue_length - 10} more*"
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting MCP queue: {e}")
            return f"❌ Error: {str(e)}"
    
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
