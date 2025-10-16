# 🎵 Jarvis Music Bot Commands

Complete list of music commands available in the Discord bot.

## 🎶 Playback Commands

### `/play [song_name]`
Play a song in your voice channel.
- **With song name**: Plays the specified song and auto-queues 5 random songs
- **Without song name**: 
  - If paused: Resumes playback
  - If not playing: Starts playing 5 random songs
- **Example**: `/play 90210`
- **Auto-Queue**: Automatically adds 5 random songs to queue when you start playing

### `/pause`
Pause the currently playing song.

### `/resume`
Resume playback if paused.

### `/stop`
Stop playback completely and clear the queue.

### `/skip`
Skip to the next song in the queue.

### `/random` or `/shuffle`
Add a random song to the queue (or start playing if nothing is playing).
- Queues 1 random song at a time
- Use multiple times to queue more songs

---

## 📜 Queue Management

### `/queue`
View the current music queue.

### `/queue [song_name]`
Add a song to the queue.
- **Example**: `/queue Flawless`

### `/queue clear`
Clear all songs from the queue.

### `/queue remove [position]`
Remove a song from the queue by position (1-based).
- **Example**: `/queue remove 3`

### `/mcpqueue`
View the MCP server's queue status (for debugging).

---

## 🔍 Discovery Commands

### `/songs` or `/list`
List all available songs in the music library (first 20).

### `/findsong [keyword]`
Search for songs matching a keyword.
- **Example**: `/findsong travis`
- Returns top 3 matches

### `/nowplaying` or `/np`
Show information about the currently playing song.

---

## 🎧 Voice Channel Commands

### `/join`
Make Jarvis join your current voice channel.

### `/leave` or `/disconnect`
Make Jarvis leave the voice channel and stop playback.

### `/volume [level]`
Adjust playback volume (0-100).
- **Example**: `/volume 50`

---

## 🎯 Quick Start

1. **Join a voice channel** in Discord
2. Type `/play` to start playing 5 random songs
3. Or type `/play 90210` to play a specific song (+ 5 random songs queued)
4. Use `/random` to add more random songs to queue
5. Use `/skip` to skip to next song
6. Use `/pause` to pause, then `/play` to resume
7. Use `/leave` when done

**Pro Tip**: The bot auto-queues 5 random songs when you start playing, so you always have music lined up!

---

## 🔧 Technical Details

### MCP Tools Used
- `play_song` - Get song path and metadata
- `play_random` - Get a random song
- `search_song` - Find songs by keyword
- `list_songs` - Get all available songs
- `add_to_queue` - Add song to MCP queue
- `get_queue` - Get MCP queue status
- `clear_queue` - Clear MCP queue
- `remove_from_queue` - Remove song from MCP queue
- `play_next_in_queue` - Play next queued song

### Supported Audio Formats
- MP3 (`.mp3`)
- FLAC (`.flac`)
- WAV (`.wav`)
- M4A (`.m4a`)
- OGG (`.ogg`)
- AAC (`.aac`)
- WMA (`.wma`)

### Requirements
- FFmpeg must be installed and in system PATH
- Discord bot must have voice channel permissions
- Music MCP server must be running and connected

---

## 🐛 Troubleshooting

### "FFmpeg not found"
- Install FFmpeg: `winget install ffmpeg`
- Add FFmpeg to system PATH
- Restart the Discord bot

### "Song not found"
- Use `/songs` to see available tracks
- Use `/findsong [keyword]` to search
- Check exact song name spelling

### "Not in a voice channel"
- Join a voice channel first
- Make sure the bot has permission to join

### Music not playing
- Check if FFmpeg is in PATH
- Verify music files exist in the configured folder
- Check bot logs for detailed errors

---

## 📝 Notes

- The bot will automatically join your voice channel when you use `/play`
- Songs are queued automatically if something is already playing
- The queue persists until cleared or the bot leaves
- Use `/mcpqueue` to debug MCP server queue issues
- Search is case-insensitive and matches partial names

