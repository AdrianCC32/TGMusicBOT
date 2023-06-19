import discord
from discord.ext import commands
from googleapiclient.discovery import build
import random
import youtube_dl
import os
from urllib.parse import parse_qs, urlparse
from dotenv import load_dotenv
import warnings

warnings.filterwarnings("ignore")
load_dotenv()
bot_token1 = os.getenv('BOT_TOKEN')
api_key1 = os.getenv('API_KEY')

intents = discord.Intents.default()
intents.message_content = True
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='.', intents=intents)

songs_queue = [] 

API_KEY = api_key1

async def wait_for_music_end(ctx, voice_channel):
    if voice_channel.is_playing():
        await bot.wait_for('voice_state_update')
        await wait_for_music_end(ctx, voice_channel)
    return None

async def play_music(ctx):
    voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_channel and voice_channel.is_playing():
        await wait_for_music_end(ctx, voice_channel)    
    else:
        if voice_channel and voice_channel.is_connected():
            await voice_channel.move_to(ctx.author.voice.channel)
        else:
            voice_channel = await ctx.author.voice.channel.connect()

        if len(songs_queue) > 0:
            song = songs_queue.pop(0)
            await play_song(song, voice_channel)
        else:
            await ctx.send("No hay canciones en la cola de reproducción.")


async def play_song(song, voice_channel):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        ydl = youtube_dl.YoutubeDL(ydl_opts)
        info = ydl.extract_info(song, download=False)
        url = info['formats'][0]['url']

        voice_channel.play(discord.FFmpegPCMAudio(url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"),
                            after=lambda error: bot.loop.create_task(play_next(error, voice_channel)))
    except Exception as e:
        print(f'Error al reproducir la música: {e}')


async def play_next(error, voice_channel):
    if error:
        print(f'Error en la reproducción: {error}')
    
    if len(songs_queue) > 0:
        song = songs_queue.pop(0)
        await play_song(song, voice_channel)
    else:
        pass

async def add_to_queue(ctx):
    query = ' '.join(ctx.message.content.split()[1:])  
    await ctx.send('Buscando música en YouTube...')

    video_url = await search_video(query)

    if video_url:
        songs_queue.append(video_url)
        await ctx.send(f'Canción añadida a la cola de reproducción: {query}')
    else:
        await ctx.send('No se encontró ningún video de YouTube para la búsqueda especificada.')

async def add_playlist_to_queue(ctx, playlist_url):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        playlist_id = playlist_url.split("list=")[1]
        request = youtube.playlistItems().list(part='snippet', maxResults=50, playlistId=playlist_id)
        response = request.execute()

        for item in response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            songs_queue.append(video_url)

        await ctx.send("Playlist añadida correctamente a la cola de reproducción.")
    except Exception as e:
        print(f"Error al añadir la playlist a la cola de reproducción: {e}")



async def search_video(query):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.search().list(
        part='id',
        q=query,
        type='video',
        maxResults=1
    )
    response = request.execute()
    if 'items' in response and len(response['items']) > 0:
        video_id = response['items'][0]['id']['videoId']
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        return video_url
    return None


@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')


@bot.command(aliases=['p'])
async def play(ctx, *, query: str):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("Debes estar en un canal de voz para usar este comando.")
        return

    if "youtube.com/playlist" in query:
        await add_playlist_to_queue(ctx, query)
    else:
        await add_to_queue(ctx, query)

    await play_music(ctx)

@bot.command(aliases = ['m','mv'])
async def move(ctx, position: int):
    if len(songs_queue) > 0 and 1 <= position <= len(songs_queue):
        song = songs_queue.pop(position - 1)
        songs_queue.insert(0, song)
        await ctx.send("La canción ha sido movida correctamente.")
    else:
        await ctx.send("La posición especificada es inválida o no hay canciones en la cola de reproducción.")



@bot.command(aliases=['q'])
async def queue(ctx):
    if not songs_queue:
        await ctx.send("No hay canciones en la cola de reproducción.")
        return

    queue_list = [f"{i+1}.- {get_song_title(url)}" for i, url in enumerate(songs_queue)]
    messages = []
    current_message = ""

    for song in queue_list:
        if len(current_message) + len(song) + 1 <= 2000:
            current_message += song + "\n"
        else:
            messages.append(current_message)
            current_message = song + "\n"

    if current_message:
        messages.append(current_message)

    for message in messages:
        await ctx.send(message)

def get_video_id(url):
    query_string = urlparse(url)
    if query_string.hostname == "youtu.be":
        return query_string.path[1:]
    if query_string.hostname in ("www.youtube.com", "youtube.com"):
        if query_string.path == "/watch":
            p = parse_qs(query_string.query)
            return p["v"][0]
        if query_string.path[:7] == "/embed/":
            return query_string.path.split("/")[2]
        if query_string.path[:3] == "/v/":
            return query_string.path.split("/")[2]
    return None


def get_song_title(url):
    try:
        video_id = get_video_id(url)
        youtube = build("youtube", "v3", developerKey=API_KEY)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        if "items" in response and len(response["items"]) > 0:
            title = response["items"][0]["snippet"]["title"]
            return title
    except Exception as e:
        print(f"Error al obtener el título de la canción: {e}")
    return "Título desconocido"



@bot.command(aliases = ['s', 'fs'])
async def skip(ctx):
    voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_channel and voice_channel.is_playing():
        voice_channel.stop()
        await ctx.send('Canción omitida.')
    else:
        await ctx.send('No hay canción reproduciéndose actualmente.')

@bot.command(aliases = ['r'])
async def remove(ctx, position: int):
    if len(songs_queue) > 0 and 1 <= position <= len(songs_queue):
        removed_song = songs_queue.pop(position - 1)
        await ctx.send(f"La canción en la posición {position} ha sido removida: {get_song_title(removed_song)}")
    else:
        await ctx.send("La posición especificada es inválida o no hay canciones en la cola de reproducción.")


@bot.command()
async def join(ctx):
    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client:
            if voice_client.channel != channel:
                await voice_client.move_to(channel)
        else:
            await channel.connect()
    else:
        await ctx.send("Debes estar en un canal de voz para usar este comando.")


@bot.command(aliases = ['random'])
async def shuffle(ctx):
    global songs_queue
    if len(songs_queue) > 0:
        random.shuffle(songs_queue)
        await ctx.send('Lista de reproducción mezclada.')
    else:
        await ctx.send('No hay canciones en la cola de reproducción.')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("Ocurrió un error al ejecutar el comando. Por favor, intenta nuevamente.")
        print(f"Error al ejecutar el comando: {error.original}")
    else:
        await ctx.send(f"Error: {error}")


bot.run(bot_token1)
