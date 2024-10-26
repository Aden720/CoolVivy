import asyncio
import json
import os
import re

import discord
from discord import app_commands
from discord.ext import commands
from ytmusicapi import YTMusic

from bandcamp_utils import getBandcampParts
from general_utils import (
    formatMillisecondsToDurationString,
    formatTimeToDisplay,
    formatTimeToTimestamp,
)
from soundcloud_utils import getSoundcloudParts
from spotify_utils import getSpotifyParts

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ownerUser = str(os.getenv("OWNER_USER_ID"))
testInstance = os.getenv("TEST_INSTANCE", "False")
servers = os.getenv("SERVERS")
if servers:
    server_whitelist = json.loads(servers)
else:
    server_whitelist = []
    print("SERVERS is not set in the environment variables.")


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    # Sync commands to make sure they are registered
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')


@bot.event
async def on_message(message):
    if message.author == bot.user or (testInstance == "True" and str(
            message.author.id) != ownerUser) or message.author.bot is True:
        # or (testInstance == 'False' and str(message.author.id) == user2):
        return
    elif bot.user and (str(bot.user.id) in message.content):
        if 'hello' in message.content.lower():
            await message.channel.send('Hello!')
        else:
            await message.channel.send(
                f'Ask <@{ownerUser}> for help.'
                if ownerUser else 'Use **/help** for help.')
    elif str(message.guild.id) in server_whitelist:
        await asyncio.sleep(3)
        try:
            await fetchEmbed(message, False)
        except Exception as e:
            print(f'Error: {e}')


async def fetchWebhook(message):
    # Check if the bot has the correct permissions to manage webhooks
    canSend = message.channel.permissions_for(message.guild.me).manage_webhooks
    if not canSend:
        await message.author.send(
            "I do not have permission to manage webhooks!\n"
            "Ask the server owners to give me the permission to manage webhooks"
            " so I can send less cluttered messages to the channel.")
        return None
    # Create a webhook
    webhook = None
    channel = message.channel.parent if hasattr(message.channel,
                                                'parent') else message.channel
    webhooks = await channel.webhooks()
    if len(webhooks) > 0:
        for hook in webhooks:
            if hook.token is not None:
                webhook = hook
                break

    if webhook is None:
        webhook = await channel.create_webhook(name='CoolVivy embed')

    return webhook


async def fetchEmbed(message, isInteraction):
    newMessage = await message.channel.fetch_message(message.id)
    embeds = []
    webhook = None
    if not isInteraction:
        webhook = await fetchWebhook(message)
    canUseWebhook = webhook is not None

    for embed in newMessage.embeds:
        if any(
                word in embed.url for word in
            ['soundcloud.com', 'youtube.com', 'spotify.com', 'bandcamp.com']):
            #get all embed fields
            fieldParts = getDescriptionParts(embed)
            if not fieldParts:
                raise Exception('No data found')

            #create a new embed
            embedVar = discord.Embed(
                title=fieldParts.get('title', embed.title),
                description=fieldParts.get('description'),
                color=fieldParts.get('embedColour', 0x00dcff),
                url=embed.url)

            #add platform link if applicable
            setAuthorLink(embedVar, fieldParts.get('embedPlatformType'))

            #thumbnail
            thumbnailUrl = fieldParts.get('thumbnailUrl')
            if thumbnailUrl:
                embedVar.set_thumbnail(url=thumbnailUrl)
            elif embed.thumbnail:
                embedVar.set_thumbnail(url=embed.thumbnail.url)

            #populate embed fields
            for key, value in fieldParts.items():
                if key not in [
                        'description', 'title', 'thumbnailUrl',
                        'embedPlatformType', 'embedColour'
                ]:
                    inline = key not in ['Tags', 'Description']
                    embedVar.add_field(name=key, value=value, inline=inline)

            #remove embed from original message
            if not isInteraction and fieldParts.get(
                    'embedPlatformType') == 'bandcamp':
                await message.edit(suppress=True)

            #react to message
            if isInteraction:
                emoji_id = os.getenv("EMOJI_ID")
                emoji = bot.get_emoji(int(emoji_id)) if emoji_id else '🔗'
                await message.add_reaction(emoji)

            #send embed
            if isInteraction:
                return embedVar
            else:
                if canUseWebhook:
                    embeds.append(embedVar)
                    continue
                await message.channel.send(embed=embedVar)
        else:
            raise Exception(
                "This doesn't seem to be a supported URL.\nCurrently only "
                "Bandcamp, SoundCloud, Spotify and YouTube are supported.")
    if canUseWebhook and len(embeds) > 0:
        embeds[-1].set_footer(text=f'Powered by CoolVivy {message.author.id}',
                              icon_url=message.channel.guild.me.avatar.url)
        if hasattr(message.channel, 'parent'):
            await webhook.send(content=message.content,
                               embeds=embeds,
                               username=message.author.display_name,
                               avatar_url=message.author.avatar.url,
                               thread=message.channel)
        else:
            await webhook.send(
                content=message.content,
                embeds=embeds,
                username=message.author.display_name,
                avatar_url=message.author.avatar.url,
            )
        #remove original message
        await message.delete()


#Check if it's a Youtube Music track based on track type
def isYoutubeMusic(type):
    #MUSIC_VIDEO_TYPE_ATV
    #MUSIC_VIDEO_TYPE_OMV
    #MUSIC_VIDEO_TYPE_UGC
    #MUSIC_VIDEO_TYPE_OFFICIAL_SOURCE_MUSIC
    return type and type in ['MUSIC_VIDEO_TYPE_ATV', 'MUSIC_VIDEO_TYPE_OMV']


def getYouTubeParts(embed):
    youtubeParts = {'embedPlatformType': 'youtube', 'embedColour': 0xff0000}
    ytmusic = YTMusic()
    videoId = re.search(r'watch\?v=([^&]*)', embed.url) or re.search(
        'shorts/([^&]*)', embed.url)
    description = embed.description
    track = None
    if videoId is not None:
        videoId = videoId.group(1)
        track = ytmusic.get_song(videoId)

        #Title
        videoTitle = track['videoDetails']['title']
        if videoTitle:
            youtubeParts['title'] = videoTitle

        #Artist/Channel
        videoType = track['videoDetails'].get('musicVideoType')
        author = track['videoDetails']['author']
        channelId = track['videoDetails']['channelId']
        isYoutubeMusicTrack = isYoutubeMusic(videoType)
        if isYoutubeMusicTrack:
            youtubeParts['embedPlatformType'] = 'youtubemusic'
            youtubeParts[
                'Artist'] = f'[{author}](https://music.youtube.com/channel/{channelId})'
        else:
            youtubeParts[
                'Channel'] = f'[{embed.author.name}]({embed.author.url})'

        #Duration
        videoDuration = track['videoDetails']['lengthSeconds']
        if videoDuration:
            youtubeParts['Duration'] = formatMillisecondsToDurationString(
                int(videoDuration) * 1000)

        #Description
        # videoDescription = track['microformat']['microformatDataRenderer'][
        #     'description']
        # if videoDescription:
        #     description = track['microformat']['microformatDataRenderer'][
        #         'description']

        #Square Thumbnail
        videoThumbnail = track['videoDetails']['thumbnail']['thumbnails'][-1]
        youtubeParts['thumbnailUrl'] = (
            videoThumbnail['url'] if videoThumbnail['width']
            == videoThumbnail['height'] else embed.thumbnail.url)

    else:
        playlistId = re.search(r'playlist\?list=([^&]*)', embed.url)
        if playlistId is not None:
            playlistId = playlistId.group(1)
            playlistId = ytmusic.get_album_browse_id(playlistId)
            if playlistId:
                track = ytmusic.get_album(playlistId)
                if track:
                    #youtube music playlist
                    youtubeParts['embedPlatformType'] = 'youtubemusic'
                    #Title
                    albumTitle = track['title']
                    if albumTitle:
                        youtubeParts['title'] = albumTitle

                    #Artists
                    albumArtists = track['artists']
                    youtubeParts[
                        f'Artist{"s" if len(albumArtists) > 1 else ""}'] = ', '.join(
                            [
                                f'[{artist["name"]}](https://music.youtube.com/channel/{artist["id"]})'
                                for artist in albumArtists
                            ])

                    #Type
                    albumType = track['type']
                    if albumType:
                        youtubeParts['Type'] = albumType

                    #Tracks
                    albumTrackCount = track['trackCount']
                    if albumTrackCount:
                        youtubeParts['Tracks'] = (
                            f'{albumTrackCount} song'
                            f'{"s" if albumTrackCount > 1 else ""}')

                    #Duration
                    albumDuration = track['duration_seconds']
                    if albumDuration:
                        youtubeParts[
                            'Duration'] = formatMillisecondsToDurationString(
                                int(albumDuration) * 1000)

                    #Released
                    albumReleaseDate = track['year']
                    if albumReleaseDate:
                        youtubeParts['Released'] = formatTimeToDisplay(
                            albumReleaseDate, '%Y')

                    #Description
                    albumDescription = track['description']
                    if albumDescription:
                        description = track['description']

                    #Square Thumbnail
                    youtubeParts['thumbnailUrl'] = track['thumbnails'][-1][
                        'url']
                else:
                    #non-youtube music playlist
                    youtubeParts['embedPlatformType'] = 'youtube'

    if description:
        descriptionMatch = re.search('.+?\n\n(.+?)\n.*Released on: (.*?)\n',
                                     description, re.S)
        if descriptionMatch:
            otherArtists = descriptionMatch.group(1).split(' · ')
            if len(otherArtists) > 2:
                otherArtists = otherArtists[2:]
                youtubeParts['Other Artists'] = ', '.join(otherArtists)
                #Reorder the fields
                temp = youtubeParts.pop('Duration')
                youtubeParts['Duration'] = temp

            youtubeParts['Released on'] = formatTimeToDisplay(
                descriptionMatch.group(2), '%Y-%m-%d')

    if not (youtubeParts.get('Released on')
            or youtubeParts.get('Released')) and track is not None:
        timestamp = formatTimeToTimestamp(
            track['microformat']['microformatDataRenderer']['uploadDate'])
        youtubeParts['Uploaded on'] = formatTimeToDisplay(
            timestamp, '%Y-%m-%dT%H:%M:%S')

    return youtubeParts


def getDescriptionParts(embed):
    if 'soundcloud.com' in embed.url:
        return getSoundcloudParts(embed)
    elif 'youtube.com' in embed.url:
        return getYouTubeParts(embed)
    elif 'spotify.com' in embed.url:
        return getSpotifyParts(embed)
    else:  #Bandcamp
        if re.match('https?://bandcamp.com.+', embed.url):
            return None
        return getBandcampParts(embed)


def setAuthorLink(embedMessage, embedType):
    if embedType == 'soundcloud':
        embedMessage.set_author(
            name='SoundCloud',
            url='https://soundcloud.com/',
            icon_url='https://soundcloud.com/pwa-round-icon-192x192.png')
    elif embedType == 'youtube':
        embedMessage.set_author(
            name='YouTube',
            url='https://www.youtube.com/',
            icon_url=
            'https://www.youtube.com/s/desktop/0c61234c/img/favicon_144x144.png'
        )
    elif embedType == 'youtubemusic':
        embedMessage.set_author(
            name='YouTube Music',
            url='https://music.youtube.com/',
            icon_url=
            'https://www.gstatic.com/youtube/media/ytm/images/applauncher/music_icon_144x144.png'
        )
    elif embedType == 'spotify':
        embedMessage.set_author(
            name='Spotify',
            url='https://open.spotify.com/',
            icon_url=
            'https://open.spotifycdn.com/cdn/images/icons/Spotify_256.17e41e58.png'
        )
    else:
        embedMessage.set_author(
            name='Bandcamp',
            url='https://bandcamp.com/',
            icon_url='https://s4.bcbits.com/img/favicon/favicon-32x32.png')


#Allow user to delete a message related to them or the bot, for cleanup
@bot.tree.context_menu(name='delete message')
async def delete_bot_message(interaction: discord.Interaction,
                             message: discord.Message):
    # if (testInstance == 'True' and str(interaction.user.id) != user2):  # or (
    #     #testInstance == 'False' and str(interaction.user.id) == user2):
    #     return
    try:
        canDelete = False
        if (bot.user and message.author.id == bot.user.id) or \
           (message.author.id == interaction.user.id):
            canDelete = True
        elif message.author.bot is True and len(message.embeds) > 0:
            embed = message.embeds[-1]
            if embed.footer is not None:
                # Regex to match 'Powered by Vivy 126532652625'
                powered_by_vivy_regex = re.compile(
                    r"Powered by CoolVivy (\d+)")
                match = powered_by_vivy_regex.search(str(embed.footer.text))
                # check the user id matches
                if match and match.group(1) == str(interaction.user.id):
                    canDelete = True
        if canDelete:
            await message.delete()
            # await interaction.response.send_message(content='Attempting to delete...',
            #     ephemeral=True)
            await interaction.response.send_message(content='Message deleted',
                                                    ephemeral=True)
        else:
            await interaction.response.send_message(
                content=
                '''This message is not from me or a reformatted message from you.
                I can only delete messages from me or posted by you.''',
                ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(content=str(e), ephemeral=True)


# Define a context menu for getting embed metadata
@bot.tree.context_menu(name='get track metadata')
async def fetch_embed_message(interaction: discord.Interaction,
                              message: discord.Message):
    if (testInstance == 'True'
            and str(interaction.user.id) != ownerUser):  # or (
        #testInstance == 'False' and str(interaction.user.id) == user2):
        return
    await interaction.response.send_message(
        content=f'Fetching details for {message.jump_url}', ephemeral=True)
    try:
        if message.author.id == interaction.user.id:
            await fetchEmbed(message, False)
        else:
            trackEmbed = await fetchEmbed(message, True)
            if trackEmbed:
                await interaction.followup.send(
                    content=interaction.user.mention, embed=trackEmbed)
    except Exception as e:
        await interaction.followup.send(content=str(e), ephemeral=True)


@bot.tree.command(name="help", description="Show help information")
async def help_command(interaction: discord.Interaction):
    help_text = """I provide information about track links and albums.

__**How to use**__
On any track link from Soundcloud, Spotify, Bandcamp or YouTube:
1. Right click/hold a message
1. Select **Apps**
1. Select **get track metadata**.
    - You can clean up messages I've sent by selecting the **delete message** option.
    """.strip()
    await interaction.response.send_message(help_text, ephemeral=True)


try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("Please add your token to the Secrets pane.")
    bot.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        print(
            "The Discord servers denied the connection for making too many requests"
        )
        print(
            "Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests"
        )
    else:
        raise e
