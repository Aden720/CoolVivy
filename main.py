import os
import re
import math
import discord
import asyncio
from ytmusicapi import YTMusic
from sclib import SoundcloudAPI, Track, Playlist
from datetime import datetime
from bandcamp import BandcampScraper

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

user1 = str(os.getenv("USER1"))
user2 = str(os.getenv("USER2"))
testInstance = os.getenv("TEST_INSTANCE")


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user or (testInstance == "True"
                                         and str(message.author.id) != user2):
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
                    color=0x00dcff,
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
                            'embedPlatformType'
                    ]:
                        inline = key not in ['Tags', 'Description']
                        embedVar.add_field(name=key,
                                           value=value,
                                           inline=inline)

                #send embed
                await message.channel.send(embed=embedVar)

                #react to message
                if len(message.reactions) > 0:
                    emoji_id = os.getenv("EMOJI_ID")
                    emoji = client.get_emoji(
                        int(emoji_id)) if emoji_id else '🔗'
                    await message.add_reaction(emoji)


def cleanLinks(description):
    return re.sub(r'(https?:\/\/[a-zA-Z0-9\-\.]*[^\s]*)', r'<\1>', description)


def formatTimeToDisplay(timestamp, timeFormat):
    datetimeObject = datetime.strptime(timestamp, timeFormat)
    return datetimeObject.strftime("%d %B %Y")


def formatTimeToTimestamp(time):
    # Split the timestamp into the date-time part and the timezone part
    dateString, timezoneString = time.split('T')
    timeString, timezoneOffset = timezoneString.split(
        '-') if '-' in timezoneString else timezoneString.split('+')
    return dateString + 'T' + timeString


def split_tags(tag_string):
    # Regular expression to match tags with or without spaces
    pattern = r'"[^"]*"|\S+'
    # Find all matches using the pattern
    matches = re.findall(pattern, tag_string)
    # Remove quotes from tags that were enclosed in quotes
    tags = [tag.strip('"') for tag in matches]
    return tags


def formatMillisecondsToDurationString(milliseconds):
    (hours, seconds) = divmod(milliseconds / 1000, 3600)
    (minutes, seconds) = divmod(seconds, 60)
    timestamp = (f'{hours:02.0f}:' if hours > 0 else
                 '') + f'{minutes:02.0f}:{math.floor(seconds):02.0f}'
    return f'`{timestamp}`'


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
    spotifyParts = {'embedPlatformType': 'spotify'}
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
        youtubeParts['thumbnailUrl'] = track['videoDetails']['thumbnail'][
            'thumbnails'][-1]['url']

        #Check if it's a Youtube Music track or is a track type
        #MUSIC_VIDEO_TYPE_ATV
        #MUSIC_VIDEO_TYPE_OMV
        #MUSIC_VIDEO_TYPE_UGC
        #MUSIC_VIDEO_TYPE_OFFICIAL_SOURCE_MUSIC
        videoType = track['videoDetails'].get('musicVideoType')
        if videoType and videoType in [
                'MUSIC_VIDEO_TYPE_ATV', 'MUSIC_VIDEO_TYPE_OMV'
        ]:
            youtubeParts['embedPlatformType'] = 'youtubemusic'
        else:
            youtubeParts['embedPlatformType'] = 'youtube'
    else:
        playlistId = re.search(r'playlist\?list=([^&]*)', embed.url)
        if playlistId is not None:
            playlistId = playlistId.group(1)
            playlistId = ytmusic.get_album_browse_id(playlistId)
            if playlistId:
                track = ytmusic.get_album(playlistId)
                if track:
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

                    youtubeParts['isYouTubeMusic'] = True

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


def getSoundCloudParts(embed):
    soundcloudParts = {'embedPlatformType': 'soundcloud'}
    api = SoundcloudAPI()
    track = api.resolve(embed.url)

    if isinstance(track, Track):
        soundcloudParts['title'] = f'{track.artist} - {track.title}'
        if track.genre:
            soundcloudParts['Genre'] = f'`{track.genre}`'

        #Duration
        soundcloudParts['Duration'] = formatMillisecondsToDurationString(
            track.duration)

        #Release date
        if track.created_at:
            soundcloudParts['Uploaded on'] = formatTimeToDisplay(
                track.created_at, '%Y-%m-%dT%H:%M:%SZ')

        #Likes
        soundcloudParts['Likes'] = f':orange_heart: {track.likes_count}'

        #Plays
        soundcloudParts['Plays'] = f':notes: {track.playback_count:,}'

        #Tags
        tags = split_tags(track.tag_list)
        if len(tags) > 0:
            formatted_tags = [f'`{tag}`' for tag in tags]
            soundcloudParts['Tags'] = ', '.join(formatted_tags)

        #Buy Link
        if track.purchase_url:
            buyLinkName = track.purchase_title or 'Buy/Stream'
            isDownload = any(word in buyLinkName.lower()
                             for word in ['download', 'free', 'dl'])
            soundcloudParts['Buy/Download Link'] = (
                f'{":arrow_down:" if isDownload else ":link:"} '
                f'[{buyLinkName}]({track.purchase_url})')

        #Description
        # if track.description:
        #     soundcloudParts['Description'] = cleanLinks(track.description)

    elif isinstance(track, Playlist):
        soundcloudParts['title'] = f'{track.title}'
        soundcloudParts['description'] = 'Playlist'

        #Genre
        if track.genre:
            soundcloudParts['Genre'] = f'`{track.genre}`'

        #Likes
        soundcloudParts['Likes'] = f':orange_heart: {track.likes_count}'

        #Tracks
        soundcloudParts['Tracks'] = f'`{track.track_count}`'

        #Duration
        soundcloudParts['Duration'] = formatMillisecondsToDurationString(
            track.duration)

        #Created by
        # soundcloudParts['Created by'] = f'`{track.user["username"]}`'

        #Tags
        tags = split_tags(track.tag_list)
        if len(tags) > 0:
            formatted_tags = [f'`{tag}`' for tag in tags]
            soundcloudParts['Tags'] = ', '.join(formatted_tags)

        #Description
        # if track.description:
        #     soundcloudParts['Description'] = cleanLinks(track.description)
    else:
        soundcloudParts['Metadata'] = 'No data available.'
        if embed.description:
            soundcloudParts['Description'] = cleanLinks(embed.description)
    return soundcloudParts


def getBandcampParts(embed):
    bandcampParts = {'embedPlatformType': 'bandcamp'}
    channelUrl = re.sub(r'(https?://[a-zA-Z0-9\-]*\.bandcamp\.com).*', r'\1',
                        embed.url)
    if embed.title:
        embed.title, artist = embed.title.split(', by ')
        bandcampParts['Artist'] = artist
        if artist != 'Various Artists':
            embed.title = f'{artist} - {embed.title}'

    if embed.description:
        if embed.description.startswith('from the album'):
            bandcampParts['Album'] = embed.description.split(
                'from the album ')[-1]
        elif embed.description.startswith('track by'):
            bandcampParts['description'] = 'Single'
        else:
            bandcampParts['description'] = embed.description

    if embed.provider:
        if embed.provider.name != bandcampParts.get('Artist'):
            bandcampParts['Channel'] = (
                f'[{embed.provider.name}]'
                f'({embed.provider.url or channelUrl})')
        else:
            bandcampParts[
                'Artist'] = f'[{bandcampParts["Artist"]}]({channelUrl})'

    return bandcampParts


def getDescriptionParts(embed):
    if 'soundcloud.com' in embed.url:
        return getSoundCloudParts(embed)
    elif 'youtube.com' in embed.url:
        return getYouTubeParts(embed)
    elif 'spotify.com' in embed.url:
        return getSpotifyParts(embed)
    else:  #Bandcamp
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
