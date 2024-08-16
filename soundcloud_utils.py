import re

from sclib import Playlist, SoundcloudAPI, Track

from general_utils import (
    cleanLinks,
    formatMillisecondsToDurationString,
    formatTimeToDisplay,
)


def split_tags(tag_string):
    # Regular expression to match tags with or without spaces
    pattern = r'"[^"]*"|\S+'
    # Find all matches using the pattern
    matches = re.findall(pattern, tag_string)
    # Remove quotes from tags that were enclosed in quotes
    tags = [tag.strip('"') for tag in matches]
    return tags


def getSoundcloudParts(embed):
    soundcloudParts = {'embedPlatformType': 'soundcloud'}
    api = SoundcloudAPI()

    track = api.resolve(embed.url)

    if isinstance(track, Track):
        soundcloudParts['title'] = (track.title if track.artist in track.title
                                    else f'{track.artist} - {track.title}')
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
