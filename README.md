# Discord Music Bot

A feature-rich Discord music bot built with Python, discord.py, and yt-dlp. Supports queue management, playlist saving, loop modes, volume control, and more.

## Features

- **Music Playback**: Play songs from YouTube via search or direct URL.
- **Queue System**: Add multiple songs to a queue, view, remove, and clear.
- **Playlist Management**: Save songs to a persistent playlist per server.
- **Loop Modes**: Loop current song, loop entire queue, or no loop.
- **Volume Control**: Adjust volume from 0% to 200%.
- **Playback Controls**: Pause, resume, skip, stop.
- **Auto Leave**: Automatically leaves voice channel when empty.
- **Embedded Messages**: Beautiful Discord embeds for all responses.
- **Error Handling**: Robust error handling and user-friendly messages.

## Commands

### Music Commands
- `!join` / `!j` – Bot joins your voice channel.
- `!play` / `!p` `<query/url>` – Play a song from YouTube.
- `!queue` / `!q` – Show the current queue.
- `!skip` / `!s` – Skip to the next song.
- `!clear` / `!cl` – Clear the entire queue.
- `!remove` / `!del` `<index>` – Remove a song from queue by index.

### Playback Controls
- `!pause` – Pause the current song.
- `!resume` – Resume playback.
- `!stop` – Stop playback and clear queue.
- `!volume` / `!vol` `<0-200>` – Set volume percentage.
- `!loop` `<one/all/off>` – Set loop mode.

### Playlist Commands
- `!add` `<name>` `<url>` – Add a song to the saved playlist.
- `!plist` / `!pl` – List all songs in the playlist.
- `!removeplist` / `!rplist` `<index>` – Remove a song from playlist.
- `!playplist` / `!ppl` `<index>` – Play a song from playlist by index.

### Utility Commands
- `!status` – Show current bot status (song, queue, loop, volume).
- `!leave` / `!dc` – Bot leaves the voice channel.
- `!help` – Show this help message.

## Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg installed and added to PATH
- Discord Bot Token

### Steps
1. Clone this repository:
   
```bash
   git clone https://github.com/yourusername/discord-music-bot.git
   cd discord-music-bot
   
```

2. Install dependencies:
   
```bash
   pip install -r requirements.txt
   
```

3. Configure the bot:
   - Create a `config.json` file (or use environment variable `TOKEN`).
   - Add your Discord bot token:
     
```
json
     {
       "TOKEN": "your_bot_token_here"
     }
     
```

4. Run the bot:
   
```
bash
   python bot.py
   
```

## Configuration

The bot uses a `config.json` file for the token. Alternatively, you can set the `TOKEN` environment variable.

A template `config.example.json` is provided. Copy it to `config.json` and replace `your_bot_token_here` with your actual Discord bot token.

```bash
cp config.example.json config.json
```

Then edit `config.json`:

```json
{
  "TOKEN": "your_bot_token_here"
}
```

> **Security Note**: Never commit your real token to GitHub. The repository includes a placeholder token to prevent accidental exposure.

## Dependencies

- `discord.py>=2.0.0`
- `yt-dlp>=2023.0.0`
- `PyNaCl>=1.5.0`

## File Structure

```
discord-bot/
├── bot.py              # Main bot code
├── config.json         # Bot token configuration (create from config.example.json)
├── config.example.json # Template configuration
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore file
├── README.md          # This file
└── playlist.json      # Auto-generated playlist storage
```

## How to Get a Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a new application.
3. Navigate to the "Bot" section and create a bot.
4. Copy the token and paste it into `config.json`.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) for the Discord API wrapper.
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube audio extraction.
- The Discord community for inspiration and support.

## Support

If you encounter any issues, please open an issue on GitHub.
