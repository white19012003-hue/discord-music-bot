"""
Discord Music Bot with Queue System
Using discord.py and yt-dlp
"""

import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import json
import os
import asyncio
from typing import Optional

# ==================== CONFIGURATION ====================

# yt-dlp options for best audio quality
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

# ==================== UTILITY FUNCTIONS ====================

def load_json(filename: str) -> dict:
    """Load JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_json(filename: str, data: dict) -> bool:
    """Save JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return False

def is_youtube_url(url: str) -> bool:
    """Check if URL is from YouTube"""
    return 'youtube.com' in url or 'youtu.be' in url

# ==================== MUSIC PLAYER CLASS ====================

class MusicPlayer:
    """Class to manage music playback for a guild"""
    
    def __init__(self):
        self.voice_client: Optional[discord.VoiceClient] = None
        self.current_song: Optional[str] = None
        self.current_link: Optional[str] = None
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.queue = []
        self.loop: bool = False
        self.loop_all: bool = False
        self.volume: float = 1.0
        self.original_queue = []  # For loop all mode
    
    async def join_vc(self, channel: discord.VoiceChannel) -> bool:
        """Join a voice channel"""
        try:
            self.voice_client = await channel.connect(timeout=10, reconnect=True)
            return True
        except Exception as e:
            print(f"Error joining voice channel: {e}")
            return False
    
    async def leave_vc(self) -> None:
        """Leave the voice channel"""
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
        self.current_song = None
        self.current_link = None
        self.is_playing = False
        self.is_paused = False
        self.queue = []
        self.loop = False
        self.loop_all = False
        self.original_queue = []
    
    async def play_song(self, link: str, bot) -> Optional[str]:
        """Play a song from YouTube link"""
        try:
            # Get song info
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(link, download=False)
                if info is None:
                    return None
                
                # Handle extractors that return a playlist
                if 'entries' in info:
                    info = info['entries'][0]
                
                song_name = info.get('title', 'Unknown')
                audio_url = info.get('url')
                
                if not audio_url:
                    return None
                
                self.current_song = song_name
                self.current_link = link
                self.is_paused = False
                
                # Create audio source
                source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
                transformed = discord.PCMVolumeTransformer(source)
                transformed.volume = self.volume
                
                # Play the audio
                def after_playing(error):
                    if error:
                        print(f"Playback error: {error}")
                    # Schedule the next song
                    asyncio.run_coroutine_threadsafe(self.play_next(bot), bot.loop)
                
                self.voice_client.play(transformed, after=after_playing)
                self.is_playing = True
                
                return song_name
                
        except Exception as e:
            print(f"Error playing song: {e}")
            return None
    
    async def play_next(self, bot) -> None:
        """Play the next song in queue"""
        # Check for loop one mode
        if self.loop and self.current_link:
            song_name = await self.play_song(self.current_link, bot)
            return
        
        # Check for loop all mode
        if self.loop_all and self.original_queue:
            # Restore original queue
            if self.original_queue:
                next_song = self.original_queue.pop(0)
                self.original_queue.append(next_song)
                song_name = await self.play_song(next_song['link'], bot)
                return
        
        # Normal mode - play next in queue
        if self.queue:
            next_song = self.queue.pop(0)
            song_name = await self.play_song(next_song['link'], bot)
        else:
            self.is_playing = False
            self.current_song = None
    
    def pause_song(self) -> bool:
        """Pause the current song"""
        if self.voice_client and self.is_playing and not self.is_paused:
            self.voice_client.pause()
            self.is_paused = True
            return True
        return False
    
    def resume_song(self) -> bool:
        """Resume the paused song"""
        if self.voice_client and self.is_playing and self.is_paused:
            self.voice_client.resume()
            self.is_paused = False
            return True
        return False
    
    def stop_song(self) -> None:
        """Stop playing and clear queue"""
        if self.voice_client:
            self.voice_client.stop()
        self.is_playing = False
        self.is_paused = False
        self.queue = []
        self.original_queue = []
        self.loop = False
        self.loop_all = False
    
    def add_to_queue(self, name: str, link: str) -> None:
        """Add a song to the queue"""
        self.queue.append({'name': name, 'link': link})
        # Save for loop all mode
        if self.loop_all:
            self.original_queue.append({'name': name, 'link': link})
    
    def get_queue(self) -> list:
        """Get the current queue"""
        return self.queue
    
    def clear_queue(self) -> None:
        """Clear the queue"""
        self.queue = []
        self.original_queue = []
    
    def remove_from_queue(self, index: int) -> Optional[dict]:
        """Remove a song from queue by index"""
        try:
            if 0 <= index < len(self.queue):
                return self.queue.pop(index)
        except IndexError:
            pass
        return None
    
    def set_loop(self, mode: str) -> str:
        """Set loop mode: 'one', 'all', or 'off'"""
        if mode == 'one':
            self.loop = True
            self.loop_all = False
            return "🔂 Loop một bài"
        elif mode == 'all':
            self.loop = False
            self.loop_all = True
            self.original_queue = self.queue.copy()
            return "🔁 Loop tất cả"
        else:  # off
            self.loop = False
            self.loop_all = False
            self.original_queue = []
            return "➡️ Loop đã tắt"
    
    def set_volume(self, vol: float) -> None:
        """Set volume (0.0 to 2.0)"""
        self.volume = max(0.0, min(2.0, vol))
        if self.voice_client and self.voice_client.source:
            self.voice_client.source.volume = self.volume
    
    def get_status(self) -> dict:
        """Get current player status"""
        return {
            'current_song': self.current_song,
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'queue_length': len(self.queue),
            'loop': 'one' if self.loop else ('all' if self.loop_all else 'off'),
            'volume': int(self.volume * 100)
        }

# ==================== BOT SETUP ====================

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

# Create bot with command prefix
bot = commands.Bot(command_prefix='!', case_insensitive=True, intents=intents)

# Dictionary to store music players for each guild
players = {}

# Playlist storage file
PLAYLIST_FILE = "playlist.json"

def get_player(guild_id: int) -> MusicPlayer:
    """Get or create music player for a guild"""
    if guild_id not in players:
        players[guild_id] = MusicPlayer()
    return players[guild_id]

# ==================== EMBED HELPERS ====================

def create_embed(title: str, description: str, color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """Create a Discord embed"""
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="🎵 Discord Music Bot")
    return embed

# ==================== BOT COMMANDS ====================

@bot.command(name="join", aliases=["j"])
async def join(ctx: commands.Context):
    """Join voice channel"""
    if not ctx.author.voice:
        embed = create_embed("❌ Lỗi", "Bạn cần vào voice channel trước!", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    channel = ctx.author.voice.channel
    player = get_player(ctx.guild.id)
    
    if player.voice_client and player.voice_client.is_connected():
        embed = create_embed("ℹ️ Thông báo", f"Bot đã ở trong voice channel {player.voice_client.channel}", discord.Color.yellow())
        await ctx.send(embed=embed)
        return
    
    success = await player.join_vc(channel)
    if success:
        embed = create_embed("✅ Thành công", f"Đã join voice channel: {channel.name}", discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = create_embed("❌ Lỗi", "Không thể join voice channel!", discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="play", aliases=["p"])
async def play(ctx: commands.Context, *, query: str = None):
    """Play music from YouTube"""
    if not query:
        embed = create_embed("❌ Lỗi", "Vui lòng nhập tên bài hát hoặc link YouTube!", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    if not ctx.author.voice:
        embed = create_embed("❌ Lỗi", "Bạn cần vào voice channel trước!", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    channel = ctx.author.voice.channel
    player = get_player(ctx.guild.id)
    
    # Join voice channel if not connected
    if not player.voice_client or not player.voice_client.is_connected():
        success = await player.join_vc(channel)
        if not success:
            embed = create_embed("❌ Lỗi", "Không thể join voice channel!", discord.Color.red())
            await ctx.send(embed=embed)
            return
    
    # Check if query is a URL
    if is_youtube_url(query):
        link = query
    else:
        # Search for the song
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if info and 'entries' in info:
                    link = info['entries'][0]['url']
                else:
                    embed = create_embed("❌ Lỗi", "Không tìm thấy bài hát!", discord.Color.red())
                    await ctx.send(embed=embed)
                    return
        except Exception as e:
            embed = create_embed("❌ Lỗi", f"Lỗi tìm kiếm: {str(e)}", discord.Color.red())
            await ctx.send(embed=embed)
            return
    
    # Get song name
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(link, download=False)
            if info and 'entries' in info:
                info = info['entries'][0]
            song_name = info.get('title', 'Unknown') if info else query
    except:
        song_name = query
    
    # Add to queue if already playing
    if player.is_playing:
        player.add_to_queue(song_name, link)
        queue_num = len(player.queue)
        embed = create_embed(
            "📝 Thêm vào queue",
            f"**{song_name}**\n📍 Vị trí: #{queue_num}",
            discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        # Play directly
        player.add_to_queue(song_name, link)
        song_name = await player.play_song(link, bot)
        if song_name:
            embed = create_embed(
                "▶️ Đang phát",
                f"**{song_name}**",
                discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = create_embed("❌ Lỗi", "Không thể phát bài hát!", discord.Color.red())
            await ctx.send(embed=embed)

@bot.command(name="queue", aliases=["q", "listqueue"])
async def queue(ctx: commands.Context):
    """Show the current queue"""
    player = get_player(ctx.guild.id)
    
    if not player.queue and not player.current_song:
        embed = create_embed("📭 Queue trống", "Không có bài hát nào trong queue!", discord.Color.yellow())
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(title="📋 Danh sách chờ", color=discord.Color.blue())
    
    # Current song
    if player.current_song:
        status = "⏸️ Tạm dừng" if player.is_paused else "🔊 Đang phát"
        embed.add_field(
            name=f"{status} - Hiện tại",
            value=f"🎵 **{player.current_song}**",
            inline=False
        )
    
    # Queue
    if player.queue:
        queue_list = "\n".join([f"{i+1}. {song['name']}" for i, song in enumerate(player.queue)])
        embed.add_field(
            name=f"⏳ Queue ({len(player.queue)} bài)",
            value=queue_list,
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name="skip", aliases=["s", "next"])
async def skip(ctx: commands.Context):
    """Skip to the next song"""
    player = get_player(ctx.guild.id)
    
    if not player.voice_client or not player.is_playing:
        embed = create_embed("❌ Lỗi", "Không có bài hát nào đang phát!", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    player.voice_client.stop()
    
    if player.queue or player.loop_all:
        embed = create_embed("⏭️ Skip", "Đã chuyển sang bài tiếp theo!", discord.Color.green())
    else:
        embed = create_embed("⏭️ Skip", "Queue đã hết, dừng phát!", discord.Color.yellow())
    
    await ctx.send(embed=embed)

@bot.command(name="clear", aliases=["cl"])
async def clear(ctx: commands.Context):
    """Clear the queue"""
    player = get_player(ctx.guild.id)
    player.clear_queue()
    
    embed = create_embed("🗑️ Đã xóa queue", "Danh sách chờ đã được xóa!", discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="remove", aliases=["del"])
async def remove(ctx: commands.Context, index: int = None):
    """Remove a song from queue by index"""
    if index is None:
        embed = create_embed("❌ Lỗi", "Vui lòng nhập số thứ tự bài hát cần xóa!", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    player = get_player(ctx.guild.id)
    
    if not player.queue:
        embed = create_embed("❌ Lỗi", "Queue trống!", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    removed = player.remove_from_queue(index - 1)  # Convert to 0-based index
    
    if removed:
        embed = create_embed("🗑️ Đã xóa", f"Đã xóa: **{removed['name']}**", discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = create_embed("❌ Lỗi", "Vị trí không hợp lệ!", discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="loop")
async def loop(ctx: commands.Context, mode: str = None):
    """Set loop mode: one, all, off"""
    player = get_player(ctx.guild.id)
    
    if not mode:
        # Show current loop status
        current = player.loop if player.loop else (player.loop_all if player.loop_all else 'off')
        status_map = {'one': '🔂 Loop một bài', 'all': '🔁 Loop tất cả', 'off': '➡️ Loop đã tắt'}
        embed = create_embed("🔁 Trạng thái loop", status_map.get(current, "Không rõ"), discord.Color.blue())
        await ctx.send(embed=embed)
        return
    
    mode = mode.lower()
    if mode not in ['one', 'all', 'off']:
        embed = create_embed("❌ Lỗi", "Chế độ không hợp lệ! Dùng: one, all, hoặc off", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    result = player.set_loop(mode)
    embed = create_embed("🔁 Đã đặt loop", result, discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="volume", aliases=["vol"])
async def volume(ctx: commands.Context, vol: int = None):
    """Set volume (0-200)"""
    if vol is None:
        player = get_player(ctx.guild.id)
        embed = create_embed("🔊 Volume", f"Volume hiện tại: **{int(player.volume * 100)}%**", discord.Color.blue())
        await ctx.send(embed=embed)
        return
    
    if vol < 0 or vol > 200:
        embed = create_embed("❌ Lỗi", "Volume phải từ 0 đến 200!", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    player = get_player(ctx.guild.id)
    player.set_volume(vol / 100)
    
    embed = create_embed("🔊 Volume", f"Đã đặt volume: **{vol}%**", discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="pause")
async def pause(ctx: commands.Context):
    """Pause the current song"""
    player = get_player(ctx.guild.id)
    
    if player.pause_song():
        embed = create_embed("⏸️ Tạm dừng", f"**{player.current_song}** đã tạm dừng", discord.Color.yellow())
        await ctx.send(embed=embed)
    else:
        embed = create_embed("❌ Lỗi", "Không thể tạm dừng! Có thể không có bài đang phát.", discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="resume", aliases=["unpause"])
async def resume(ctx: commands.Context):
    """Resume the paused song"""
    player = get_player(ctx.guild.id)
    
    if player.resume_song():
        embed = create_embed("▶️ Tiếp tục", f"**{player.current_song}** đã tiếp tục", discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = create_embed("❌ Lỗi", "Không thể tiếp tục! Có thể không có bài đang tạm dừng.", discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="stop")
async def stop(ctx: commands.Context):
    """Stop playing and clear queue"""
    player = get_player(ctx.guild.id)
    player.stop_song()
    
    embed = create_embed("⏹️ Đã dừng", "Đã dừng phát và xóa queue!", discord.Color.red())
    await ctx.send(embed=embed)

@bot.command(name="leave", aliases=["disconnect", "dc"])
async def leave(ctx: commands.Context):
    """Leave the voice channel"""
    player = get_player(ctx.guild.id)
    await player.leave_vc()
    
    embed = create_embed("👋 Rời đi", "Bot đã rời khỏi voice channel!", discord.Color.green())
    await ctx.send(embed=embed)

# ==================== PLAYLIST COMMANDS ====================

@bot.command(name="add")
async def add_song(ctx: commands.Context, name: str = None, *, link: str = None):
    """Add a song to the saved playlist"""
    if not name or not link:
        embed = create_embed("❌ Lỗi", "Cú pháp: !add <tên> <link>", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    if not is_youtube_url(link):
        embed = create_embed("❌ Lỗi", "Vui lòng nhập link YouTube hợp lệ!", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    # Load existing playlist
    playlist = load_json(PLAYLIST_FILE)
    if str(ctx.guild.id) not in playlist:
        playlist[str(ctx.guild.id)] = []
    
    # Add song
    song_info = {'name': name, 'link': link}
    playlist[str(ctx.guild.id)].append(song_info)
    
    # Save
    if save_json(PLAYLIST_FILE, playlist):
        embed = create_embed("✅ Đã thêm", f"**{name}**\n{link}", discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = create_embed("❌ Lỗi", "Không thể lưu playlist!", discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="plist", aliases=["pl", "playlist"])
async def list_playlist(ctx: commands.Context):
    """Show the saved playlist"""
    playlist = load_json(PLAYLIST_FILE)
    guild_playlist = playlist.get(str(ctx.guild.id), [])
    
    if not guild_playlist:
        embed = create_embed("📭 Playlist trống", "Chưa có bài hát nào trong playlist!", discord.Color.yellow())
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(title="📋 Playlist đã lưu", color=discord.Color.blue())
    
    song_list = "\n".join([f"{i+1}. {song['name']}" for i, song in enumerate(guild_playlist)])
    embed.add_field(name=f"Danh sách ({len(guild_playlist)} bài)", value=song_list, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="removeplist", aliases=["rplist"])
async def remove_playlist(ctx: commands.Context, index: int = None):
    """Remove a song from the saved playlist"""
    if index is None:
        embed = create_embed("❌ Lỗi", "Cú pháp: !removeplist <số>", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    playlist = load_json(PLAYLIST_FILE)
    
    if str(ctx.guild.id) not in playlist or not playlist[str(ctx.guild.id)]:
        embed = create_embed("❌ Lỗi", "Playlist trống!", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    try:
        removed = playlist[str(ctx.guild.id)].pop(index - 1)
        save_json(PLAYLIST_FILE, playlist)
        embed = create_embed("🗑️ Đã xóa", f"Đã xóa: **{removed['name']}**", discord.Color.green())
        await ctx.send(embed=embed)
    except IndexError:
        embed = create_embed("❌ Lỗi", "Vị trí không hợp lệ!", discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="playplist", aliases=["ppl"])
async def play_playlist(ctx: commands.Context, index: int = None):
    """Play a song from the saved playlist by index"""
    if index is None:
        embed = create_embed("❌ Lỗi", "Cú pháp: !playplist <số>", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    playlist = load_json(PLAYLIST_FILE)
    guild_playlist = playlist.get(str(ctx.guild.id), [])
    
    if not guild_playlist:
        embed = create_embed("❌ Lỗi", "Playlist trống!", discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    try:
        song = guild_playlist[index - 1]
        # Call play command
        ctx.message.content = f"!play {song['link']}"
        await bot.process_commands(ctx.message)
    except IndexError:
        embed = create_embed("❌ Lỗi", "Vị trí không hợp lệ!", discord.Color.red())
        await ctx.send(embed=embed)

# ==================== STATUS AND HELP ====================

@bot.command(name="status")
async def status(ctx: commands.Context):
    """Show current bot status"""
    player = get_player(ctx.guild.id)
    status = player.get_status()
    
    embed = discord.Embed(title="📊 Trạng thái Bot", color=discord.Color.blue())
    
    # Current song
    if status['current_song']:
        song_status = "⏸️ Tạm dừng" if status['is_paused'] else "🔊 Đang phát"
        embed.add_field(name="🎵 Bài đang phát", value=f"{song_status}\n{status['current_song']}", inline=False)
    
    # Queue
    queue_status = f"{status['queue_length']} bài" if status['queue_length'] > 0 else "Trống"
    embed.add_field(name="⏳ Queue", value=queue_status, inline=True)
    
    # Loop
    loop_map = {'one': '🔂 Một bài', 'all': '🔁 Tất cả', 'off': '➡️ Tắt'}
    embed.add_field(name="🔁 Loop", value=loop_map.get(status['loop'], 'Không rõ'), inline=True)
    
    # Volume
    embed.add_field(name="🔊 Volume", value=f"{status['volume']}%", inline=True)
    
    # Voice connection
    if player.voice_client and player.voice_client.is_connected():
        embed.add_field(name="📍 Voice Channel", value=str(player.voice_client.channel), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name="help", aliases=["?"])
async def help_cmd(ctx: commands.Context):
    """Show help message"""
    embed = discord.Embed(
        title="🎵 Hướng dẫn sử dụng Bot",
        description="Dưới đây là các lệnh có sẵn:",
        color=discord.Color.blue()
    )
    
    # Music commands
    embed.add_field(
        name="🎵 Lệnh phát nhạc",
        value="""`!join` - Bot join voice channel
`!play <tên/link>` - Phát nhạc từ YouTube
`!queue` - Xem danh sách chờ
`!skip` - Chuyển bài tiếp theo
`!clear` - Xóa toàn bộ queue
`!remove <số>` - Xóa bài trong queue""",
        inline=False
    )
    
    embed.add_field(
        name="⏯️ Điều khiển",
        value="""`!pause` - Tạm dừng
`!resume` - Tiếp tục phát
`!stop` - Dừng và xóa queue
`!volume <0-200>` - Điều chỉnh âm lượng""",
        inline=False
    )
    
    embed.add_field(
        name="🔁 Loop",
        value="""`!loop one` - Loop một bài
`!loop all` - Loop tất cả queue
`!loop off` - Tắt loop""",
        inline=False
    )
    
    embed.add_field(
        name="📋 Playlist",
        value="""`!add <tên> <link>` - Thêm vào playlist
`!plist` - Xem playlist đã lưu
`!removeplist <số>` - Xóa khỏi playlist
`!playplist <số>` - Phát từ playlist""",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Tiện ích",
        value="""`!status` - Xem trạng thái
`!leave` - Bot rời voice channel
`!help` - Xem hướng dẫn này""",
        inline=False
    )
    
    embed.set_footer(text="🎵 Discord Music Bot | Made with ❤️")
    await ctx.send(embed=embed)

# ==================== BOT EVENTS ====================

@bot.event
async def on_ready():
    """Bot is ready"""
    print(f"🤖 Bot đã sẵn sàng: {bot.user}")
    print(f"👤 Tên: {bot.user.name}")
    print(f"🆔 ID: {bot.user.id}")
    
    # Sync commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Đã sync {len(synced)} commands")
    except Exception as e:
        print(f"❌ Lỗi sync commands: {e}")

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """Handle voice state changes - auto leave when empty"""
    # Check if bot was in a channel
    if member.id == bot.user.id:
        return
    
    # Check if the member was the bot
    if before.channel and before.channel.guild:
        guild = before.channel.guild
        player = get_player(guild.id)
        
        # Check if channel is now empty (only bot remains)
        if before.channel.members and len(before.channel.members) == 1 and before.channel.members[0].id == bot.user.id:
            # Wait a bit to see if someone joins
            await asyncio.sleep(60)  # Wait 1 minute
            
            # Check again if still only bot
            if before.channel.members and len(before.channel.members) == 1 and before.channel.members[0].id == bot.user.id:
                await player.leave_vc()
                print(f"👋 Bot đã rời {before.channel} vì không còn ai")

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    
    if isinstance(error, commands.MissingRequiredArgument):
        embed = create_embed("❌ Thiếu tham số", f"Cú pháp đúng: `!{ctx.command.name} {ctx.command.usage}`", discord.Color.red())
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandOnCooldown):
        embed = create_embed("⏳ Chờ một chút", "Lệnh đang trong thời gian cooldown!", discord.Color.yellow())
        await ctx.send(embed=embed)
    else:
        embed = create_embed("❌ Lỗi", f"Lỗi: {str(error)}", discord.Color.red())
        await ctx.send(embed=embed)
        print(f"Command error: {error}")

# ==================== MAIN ====================

if __name__ == "__main__":
    # Get token from environment variable or config file
    token = os.environ.get("TOKEN", "")
    
    if not token:
        try:
            config = load_json("config.json")
            token = config.get("TOKEN", "")
        except:
            token = ""
    
    if not token:
        print("❌ Thiếu TOKEN! Vui lòng thêm vào file config.json hoặc biến môi trường TOKEN")
        print("📝 Tạo file config.json với nội dung:")
        print('{"TOKEN": "your_bot_token_here"}')
        exit(1)
    
    print("🎵 Đang khởi động Music Bot...")
    bot.run(token)

