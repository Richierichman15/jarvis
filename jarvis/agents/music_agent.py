#!/usr/bin/env python3
"""
MusicAgent - Specialized agent for music playback and queue management

This agent handles all music-related tasks including playback control,
queue management, song discovery, and voice channel operations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MusicAgent(AgentBase):
    """Specialized agent for music operations."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="MusicAgent",
            capabilities=[AgentCapability.MUSIC],
            version="1.0.0",
            **kwargs
        )
        
        # Music-specific configuration
        self.music_config = {
            "default_volume": 0.7,
            "max_queue_size": 100,
            "supported_formats": ["mp3", "wav", "flac", "ogg"],
            "default_playlist": "default"
        }
        
        # Music state
        self.current_song = None
        self.playlist = []
        self.queue = []
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7
        self.current_position = 0.0
        
        # Voice channel state
        self.voice_channel = None
        self.voice_client = None
        
        self.logger = logging.getLogger("agent.music")
    
    def _register_task_handlers(self):
        """Register music task handlers."""
        self.register_task_handler("play_song", self._handle_play_song)
        self.register_task_handler("play_random", self._handle_play_random)
        self.register_task_handler("search_songs", self._handle_search_songs)
        self.register_task_handler("list_songs", self._handle_list_songs)
        self.register_task_handler("add_to_queue", self._handle_add_to_queue)
        self.register_task_handler("get_queue", self._handle_get_queue)
        self.register_task_handler("pause", self._handle_pause)
        self.register_task_handler("resume", self._handle_resume)
        self.register_task_handler("stop", self._handle_stop)
        self.register_task_handler("skip", self._handle_skip)
        self.register_task_handler("set_volume", self._handle_set_volume)
        self.register_task_handler("get_status", self._handle_get_status)
        self.register_task_handler("join_voice", self._handle_join_voice)
        self.register_task_handler("leave_voice", self._handle_leave_voice)
        self.register_task_handler("shuffle_queue", self._handle_shuffle_queue)
        self.register_task_handler("clear_queue", self._handle_clear_queue)
    
    async def _initialize(self):
        """Initialize music-specific resources."""
        try:
            # Initialize music library
            await self._initialize_music_library()
            
            # Load playlists
            await self._load_playlists()
            
            # Start music monitoring
            self.music_monitor_task = asyncio.create_task(self._monitor_music_playback())
            
            self.logger.info("✅ MusicAgent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize MusicAgent: {e}")
            raise
    
    async def _cleanup(self):
        """Cleanup music resources."""
        try:
            # Stop music playback
            await self._stop_playback()
            
            # Cancel music monitoring
            if hasattr(self, 'music_monitor_task'):
                self.music_monitor_task.cancel()
                try:
                    await self.music_monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Leave voice channel
            await self._leave_voice_channel()
            
            self.logger.info("✅ MusicAgent cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during MusicAgent cleanup: {e}")
    
    async def _initialize_music_library(self):
        """Initialize the music library."""
        # This would scan for music files and build the library
        self.logger.info("🎵 Initializing music library...")
        await asyncio.sleep(0.1)  # Simulate initialization time
        
        # Sample music library
        self.music_library = [
            {
                "id": "song_001",
                "title": "90210",
                "artist": "Travis Scott",
                "album": "Rodeo",
                "duration": 320,
                "file_path": "/music/travis_scott_90210.mp3",
                "genre": "Hip-Hop"
            },
            {
                "id": "song_002", 
                "title": "SICKO MODE",
                "artist": "Travis Scott",
                "album": "ASTROWORLD",
                "duration": 312,
                "file_path": "/music/travis_scott_sicko_mode.mp3",
                "genre": "Hip-Hop"
            },
            {
                "id": "song_003",
                "title": "Goosebumps",
                "artist": "Travis Scott",
                "album": "Birds in the Trap Sing McKnight",
                "duration": 245,
                "file_path": "/music/travis_scott_goosebumps.mp3",
                "genre": "Hip-Hop"
            }
        ]
        
        self.logger.info(f"✅ Music library initialized with {len(self.music_library)} songs")
    
    async def _load_playlists(self):
        """Load playlists."""
        self.logger.info("📋 Loading playlists...")
        await asyncio.sleep(0.1)  # Simulate loading time
        
        # Sample playlists
        self.playlists = {
            "default": [song["id"] for song in self.music_library],
            "travis_scott": ["song_001", "song_002", "song_003"],
            "hip_hop": ["song_001", "song_002", "song_003"]
        }
        
        self.logger.info(f"✅ Loaded {len(self.playlists)} playlists")
    
    async def _monitor_music_playback(self):
        """Monitor music playback and handle queue progression."""
        while self.status.value == "running":
            try:
                if self.is_playing and not self.is_paused:
                    # Simulate playback progress
                    self.current_position += 1.0
                    
                    # Check if song finished
                    if self.current_song and self.current_position >= self.current_song.get("duration", 0):
                        await self._play_next_song()
                
                await asyncio.sleep(1)  # Update every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in music monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _play_next_song(self):
        """Play the next song in the queue."""
        if self.queue:
            next_song_id = self.queue.pop(0)
            song = next((s for s in self.music_library if s["id"] == next_song_id), None)
            
            if song:
                await self._start_playback(song)
            else:
                self.logger.warning(f"Song {next_song_id} not found in library")
        else:
            await self._stop_playback()
    
    async def _start_playback(self, song: Dict[str, Any]):
        """Start playing a song."""
        self.current_song = song
        self.current_position = 0.0
        self.is_playing = True
        self.is_paused = False
        
        self.logger.info(f"🎵 Now playing: {song['title']} by {song['artist']}")
    
    async def _stop_playback(self):
        """Stop music playback."""
        self.is_playing = False
        self.is_paused = False
        self.current_song = None
        self.current_position = 0.0
        
        self.logger.info("⏹️ Playback stopped")
    
    async def _join_voice_channel(self, channel_id: str):
        """Join a voice channel."""
        # This would connect to Discord voice channel
        self.voice_channel = channel_id
        self.logger.info(f"🔊 Joined voice channel: {channel_id}")
    
    async def _leave_voice_channel(self):
        """Leave the current voice channel."""
        if self.voice_channel:
            self.logger.info(f"🔇 Left voice channel: {self.voice_channel}")
            self.voice_channel = None
    
    async def _handle_task(self, task: TaskRequest) -> TaskResponse:
        """Handle music tasks."""
        try:
            handler = self.task_handlers.get(task.task_type)
            if handler:
                return await handler(task)
            else:
                raise ValueError(f"Unknown music task type: {task.task_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling music task {task.task_type}: {e}")
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_play_song(self, task: TaskRequest) -> TaskResponse:
        """Handle play song request."""
        try:
            song_name = task.parameters.get("song_name", "")
            
            # Search for song
            song = None
            if song_name:
                song = next((s for s in self.music_library 
                           if song_name.lower() in s["title"].lower() or 
                              song_name.lower() in s["artist"].lower()), None)
            
            if song:
                await self._start_playback(song)
                result = {
                    "message": f"Now playing: {song['title']} by {song['artist']}",
                    "song": song,
                    "position": 0.0
                }
            else:
                # Play random song if not found
                import random
                song = random.choice(self.music_library)
                await self._start_playback(song)
                result = {
                    "message": f"Song '{song_name}' not found. Playing random: {song['title']} by {song['artist']}",
                    "song": song,
                    "position": 0.0
                }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_play_random(self, task: TaskRequest) -> TaskResponse:
        """Handle play random song request."""
        try:
            import random
            song = random.choice(self.music_library)
            await self._start_playback(song)
            
            result = {
                "message": f"Playing random song: {song['title']} by {song['artist']}",
                "song": song,
                "position": 0.0
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_search_songs(self, task: TaskRequest) -> TaskResponse:
        """Handle song search request."""
        try:
            query = task.parameters.get("query", "").lower()
            
            if not query:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Search query is required"
                )
            
            # Search in title, artist, and album
            matching_songs = []
            for song in self.music_library:
                if (query in song["title"].lower() or 
                    query in song["artist"].lower() or 
                    query in song["album"].lower()):
                    matching_songs.append(song)
            
            result = {
                "query": query,
                "results": matching_songs,
                "total_found": len(matching_songs)
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_list_songs(self, task: TaskRequest) -> TaskResponse:
        """Handle list songs request."""
        try:
            playlist = task.parameters.get("playlist", "default")
            
            if playlist in self.playlists:
                song_ids = self.playlists[playlist]
                songs = [song for song in self.music_library if song["id"] in song_ids]
            else:
                songs = self.music_library
            
            result = {
                "playlist": playlist,
                "songs": songs,
                "total_songs": len(songs)
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_add_to_queue(self, task: TaskRequest) -> TaskResponse:
        """Handle add to queue request."""
        try:
            song_id = task.parameters.get("song_id")
            song_name = task.parameters.get("song_name")
            
            song = None
            if song_id:
                song = next((s for s in self.music_library if s["id"] == song_id), None)
            elif song_name:
                song = next((s for s in self.music_library 
                           if song_name.lower() in s["title"].lower()), None)
            
            if song:
                self.queue.append(song["id"])
                result = {
                    "message": f"Added '{song['title']}' to queue",
                    "song": song,
                    "queue_position": len(self.queue)
                }
            else:
                result = {
                    "message": "Song not found",
                    "song": None,
                    "queue_position": 0
                }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_queue(self, task: TaskRequest) -> TaskResponse:
        """Handle get queue request."""
        try:
            queue_songs = []
            for song_id in self.queue:
                song = next((s for s in self.music_library if s["id"] == song_id), None)
                if song:
                    queue_songs.append(song)
            
            result = {
                "queue": queue_songs,
                "current_song": self.current_song,
                "is_playing": self.is_playing,
                "is_paused": self.is_paused,
                "current_position": self.current_position,
                "volume": self.volume
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_pause(self, task: TaskRequest) -> TaskResponse:
        """Handle pause request."""
        try:
            if self.is_playing and not self.is_paused:
                self.is_paused = True
                message = "Music paused"
            else:
                message = "No music playing to pause"
            
            result = {
                "message": message,
                "is_playing": self.is_playing,
                "is_paused": self.is_paused,
                "current_song": self.current_song,
                "position": self.current_position
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_resume(self, task: TaskRequest) -> TaskResponse:
        """Handle resume request."""
        try:
            if self.is_paused:
                self.is_paused = False
                message = "Music resumed"
            elif not self.is_playing and self.queue:
                await self._play_next_song()
                message = "Started playing next song in queue"
            else:
                message = "No music to resume"
            
            result = {
                "message": message,
                "is_playing": self.is_playing,
                "is_paused": self.is_paused,
                "current_song": self.current_song,
                "position": self.current_position
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_stop(self, task: TaskRequest) -> TaskResponse:
        """Handle stop request."""
        try:
            await self._stop_playback()
            
            result = {
                "message": "Music stopped",
                "is_playing": self.is_playing,
                "is_paused": self.is_paused,
                "current_song": self.current_song
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_skip(self, task: TaskRequest) -> TaskResponse:
        """Handle skip request."""
        try:
            if self.is_playing:
                await self._play_next_song()
                message = "Skipped to next song"
            else:
                message = "No music playing to skip"
            
            result = {
                "message": message,
                "current_song": self.current_song,
                "is_playing": self.is_playing,
                "queue_remaining": len(self.queue)
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_set_volume(self, task: TaskRequest) -> TaskResponse:
        """Handle set volume request."""
        try:
            volume = task.parameters.get("volume", 0.7)
            volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
            
            self.volume = volume
            
            result = {
                "message": f"Volume set to {int(volume * 100)}%",
                "volume": volume
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_status(self, task: TaskRequest) -> TaskResponse:
        """Handle get status request."""
        try:
            result = {
                "is_playing": self.is_playing,
                "is_paused": self.is_paused,
                "current_song": self.current_song,
                "current_position": self.current_position,
                "volume": self.volume,
                "queue_length": len(self.queue),
                "voice_channel": self.voice_channel,
                "library_size": len(self.music_library)
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_join_voice(self, task: TaskRequest) -> TaskResponse:
        """Handle join voice channel request."""
        try:
            channel_id = task.parameters.get("channel_id")
            
            if channel_id:
                await self._join_voice_channel(channel_id)
                message = f"Joined voice channel {channel_id}"
            else:
                message = "Channel ID is required"
            
            result = {
                "message": message,
                "voice_channel": self.voice_channel
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_leave_voice(self, task: TaskRequest) -> TaskResponse:
        """Handle leave voice channel request."""
        try:
            await self._leave_voice_channel()
            
            result = {
                "message": "Left voice channel",
                "voice_channel": self.voice_channel
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_shuffle_queue(self, task: TaskRequest) -> TaskResponse:
        """Handle shuffle queue request."""
        try:
            if self.queue:
                import random
                random.shuffle(self.queue)
                message = "Queue shuffled"
            else:
                message = "Queue is empty"
            
            result = {
                "message": message,
                "queue_length": len(self.queue)
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_clear_queue(self, task: TaskRequest) -> TaskResponse:
        """Handle clear queue request."""
        try:
            queue_length = len(self.queue)
            self.queue.clear()
            
            result = {
                "message": f"Cleared {queue_length} songs from queue",
                "queue_length": len(self.queue)
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )


if __name__ == "__main__":
    # Test the MusicAgent
    async def test_music_agent():
        agent = MusicAgent()
        
        try:
            await agent.start()
            print(f"✅ MusicAgent started: {agent.get_info()}")
            
            # Test a task
            task = TaskRequest(
                task_id="test_001",
                agent_id=agent.agent_id,
                capability=AgentCapability.MUSIC,
                task_type="play_song",
                parameters={"song_name": "90210"}
            )
            
            response = await agent._handle_task(task)
            print(f"🎵 Play response: {response.result}")
            
            # Simulate running for a bit
            await asyncio.sleep(5)
            
        finally:
            await agent.stop()
            print("✅ MusicAgent stopped")
    
    asyncio.run(test_music_agent())
