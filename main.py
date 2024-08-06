import os
import re
import math
import discord
import asyncio
from ytmusicapi import YTMusic
from sclib import SoundcloudAPI, Track, Playlist
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

user1 = str(os.getenv("USER1"))
user2 = str(os.getenv("USER2"))


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user and (str(client.user.id) in message.content):
        if 'hello' in message.content.lower():
            await message.channel.send('Hello!')
        elif str(message.author.id) == user1:
            await message.channel.send('Figure it out yourself.')
        else:
            await message.channel.send(f'Ask <@{user2}> for help.')
    else:
        await asyncio.sleep(3)
        newMessage = await message.channel.fetch_message(message.id)
        for embed in newMessage.embeds:
            if any(word in embed.url for word in [
                    'soundcloud.com', 'youtube.com', 'spotify.com',
                    'bandcamp.com'
            ]):
                #get all embed fields
                fieldParts = {**getAuthor(embed), **getDescriptionParts(embed)}

                #create a new embed
                embedVar = discord.Embed(
                    title=fieldParts.get('title', embed.title),
                    description=fieldParts.get('description'),
                    color=0x00dcff)

                #populate embed fields
                for key, value in fieldParts.items():
                    if key not in ['description', 'title']:
                        inline = key not in ['Tags', 'Description']
                        embedVar.add_field(name=key,
                                           value=value,
                                           inline=inline)

                #send embed
                await message.channel.send(embed=embedVar)

                #react to message
                emoji_id = os.getenv("EMOJI_ID")
                emoji = client.get_emoji(int(emoji_id)) if emoji_id else '🔗'
                await message.add_reaction(emoji)


def cleanLinks(description):
    return re.sub(r'(https?:\/\/[a-zA-Z0-9\-\.]*[^\s]*)', r'<\1>', description)


def formatTimeToDisplay(timestamp, timeFormat):
    datetimeObject = datetime.strptime(timestamp, timeFormat)
    return datetimeObject.strftime("%d %B %Y")


def split_tags(tag_string):
    # Regular expression to match tags with or without spaces
    pattern = r'"[^"]*"|\S+'
    # Find all matches using the pattern
    matches = re.findall(pattern, tag_string)
    # Remove quotes from tags that were enclosed in quotes
    tags = [tag.strip('"') for tag in matches]
    return tags


def getAuthor(embed):
    if embed.author is not None:
        author = re.search("name='(.*?)'", str(embed.author))
        if author is not None:
            artistOrChannel, subs = re.subn('- Topic', '', author.group(1))
            return {
                ('Channel' if subs == 0 else 'Artist'):
                f'[{artistOrChannel}]({embed.author.url})'
            }
    return {}


def getSpotifyParts(embed):
    spotifyParts = {}
    attributes = ['Artist', 'Type', 'Released']
    parts = embed.description.split(' · ')
    parts[0], parts[1] = parts[1], parts[0]
    for index, attribute in enumerate(attributes):
        returnString = parts[index]
        if index == 1 and len(parts) > 3:
            type = parts[1]
            if type == 'Playlist':
                parts[2], parts[3] = parts[3], parts[2]
                attributes[2] = 'Saves'
            returnString += f' - {parts[3]}'
        spotifyParts[f'{attribute}'] = returnString
    return spotifyParts


def getYouTubeParts(embed):
    youtubeParts = {}
    if embed.description:
        description = re.search('.+?\n\n(.+?)\n.*Released on: (.*?)\n',
                                embed.description, re.S)
        if description:
            youtubeParts['Description'] = description.group(1)
            youtubeParts['Released on'] = formatTimeToDisplay(
                description.group(2), '%Y-%m-%d')
    return youtubeParts


def getSoundCloudParts(embed):
    soundcloudParts = {}
    api = SoundcloudAPI()
    track = api.resolve(embed.url)

    if isinstance(track, Track):
        soundcloudParts['title'] = f'{track.artist} - {track.title}'
        if track.genre:
            soundcloudParts['Genre'] = f'`{track.genre}`'

        #Duration
        (hours, seconds) = divmod(track.duration / 1000, 3600)
        (minutes, seconds) = divmod(seconds, 60)
        formatted = (f'{hours:02.0f}:' if hours > 0 else
                     '') + f'{minutes:02.0f}:{math.floor(seconds):02.0f}'
        soundcloudParts['Duration'] = f'`{formatted}`'

        #Release date
        if track.created_at:
            soundcloudParts['Uploaded on'] = formatTimeToDisplay(
                track.created_at, '%Y-%m-%dT%H:%M:%SZ')

        #Tags
        tags = split_tags(track.tag_list)
        if len(tags) > 0:
            formatted_tags = [f'`{tag}`' for tag in tags]
            soundcloudParts['Tags'] = ', '.join(formatted_tags)

        #Description
        if track.description:
            soundcloudParts['Description'] = cleanLinks(track.description)

    elif isinstance(track, Playlist):
        soundcloudParts['title'] = f'{track.title}'
        soundcloudParts['description'] = 'Playlist'

        #Tracks
        soundcloudParts['Tracks'] = f'`{track.track_count}`'

        #Likes
        soundcloudParts['Likes'] = f':orange_heart: {track.likes_count}'

        #Created by
        soundcloudParts['Created by'] = f'`{track.user["username"]}`'

        #Tags
        tags = split_tags(track.tag_list)
        if len(tags) > 0:
            formatted_tags = [f'`{tag}`' for tag in tags]
            soundcloudParts['Tags'] = ', '.join(formatted_tags)

        #Description
        if track.description:
            soundcloudParts['Description'] = cleanLinks(track.description)
    else:
        soundcloudParts['Metadata'] = 'No data available.'
        if embed.description:
            soundcloudParts['Description'] = cleanLinks(embed.description)
    return soundcloudParts


def getDescriptionParts(embed):
    if 'spotify.com' in embed.url:
        return getSpotifyParts(embed)
    elif 'youtube.com' in embed.url:
        return getYouTubeParts(embed)
    elif 'soundcloud.com' in embed.url:
        return getSoundCloudParts(embed)
    else:  #Bandcamp
        returnLines = {}
        if embed.description:
            returnLines['description'] = cleanLinks(embed.description)
        return returnLines


try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("Please add your token to the Secrets pane.")
    client.run(token)
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
