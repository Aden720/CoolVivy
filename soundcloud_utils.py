import re

import requests
from sclib import Playlist, SoundcloudAPI, Track

from general_utils import (
    cleanLinks,
    formatMillisecondsToDurationString,
    formatTimeToDisplay,
    remove_trailing_slash,
)


def split_tags(tag_string):
    # Regular expression to match tags with or without spaces
    pattern = r'"[^"]*"|\S+'
    # Find all matches using the pattern
    matches = re.findall(pattern, tag_string)
    # Remove quotes from tags that were enclosed in quotes
    tags = [tag.strip('"') for tag in matches]
    return tags


def fetchTrack(track_url):
    api = SoundcloudAPI()
    if track_url.startswith('https://on.soundcloud.com'):
        response = requests.get(track_url)
        if response.status_code == 200:
            track_url = response.history[0].headers['location']
        else:
            raise Exception('Unable to fetch Soundcloud Mobile URL')
    track = api.resolve(track_url)
    return track


def getSoundcloudParts(embed):
    soundcloudParts = {
        'embedPlatformType': 'soundcloud',
        'embedColour': 0xff5500
    }

    track = fetchTrack(remove_trailing_slash(embed.url))

    if isinstance(track, Track):
        artist = track.publisher_metadata.get(
            'artist',
            track.artist) if track.publisher_metadata else track.artist
        if artist.lower() in track.title.lower():
            soundcloudParts['title'] = track.title if artist.lower(
            ) == track.artist.lower() else f'{artist} - {track.title}'
        else:
            soundcloudParts['title'] = f'{artist} - {track.title}'

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

        #Buy Link
        if track.purchase_url:
            buyLinkName = track.purchase_title or 'Buy/Stream'
            isDownload = any(word in buyLinkName.lower()
                             for word in ['download', 'free', 'dl'])
            soundcloudParts['Buy/Download Link'] = (
                f'{":arrow_down:" if isDownload else ":link:"} '
                f'[{buyLinkName}]({track.purchase_url})')

        #Channel
        if track.user:
            soundcloudParts['Channel'] = (f'[{track.user["username"]}]'
                                          f'({track.user["permalink_url"]})')

        #Tags
        tags = split_tags(track.tag_list)
        if len(tags) > 0:
            formatted_tags = [f'`{tag}`' for tag in tags]
            soundcloudParts['Tags'] = ', '.join(formatted_tags)

        #Description
        # if track.description:
        #     soundcloudParts['Description'] = cleanLinks(track.description)

    elif isinstance(track, Playlist):  #set, playlist or album
        soundcloudParts['title'] = f'{track.title}'
        if (track.is_album):
            soundcloudParts['description'] = 'Album'
            soundcloudParts['Artist'] = (f'[{track.user["username"]}]'
                                         f'({track.user["permalink_url"]})')
        else:
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
