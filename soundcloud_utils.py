import re
from typing import Any, Union
from urllib.error import HTTPError

import requests
import yt_dlp
from sclib import Playlist, SoundcloudAPI, Track

from general_utils import (
    formatMillisecondsToDurationString,
    formatTimeToDisplay,
    remove_trailing_slash,
)


class YtDlpTrack:
    def __init__(self, info):
        self.title = info.get('title', 'Unknown Title')
        self.artist = info.get('uploader', info.get('artist', 'Unknown Artist'))
        self.duration = info.get('duration', 0) * 1000
        self.artwork_url = info.get('thumbnail')
        self.genre = info.get('genre')
        self.created_at = None
        upload_date = info.get('upload_date')
        if upload_date and len(upload_date) == 8:
            self.created_at = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}T00:00:00Z"
        self.likes_count = info.get('like_count')
        self.playback_count = info.get('view_count')
        self.purchase_url = None
        self.purchase_title = None
        self.downloadable = False
        self.has_downloads_left = False
        self.download_url = None
        self.tag_list = ' '.join(info.get('tags', []))
        self.publisher_metadata = None
        self.user = {
            'username': info.get('uploader', 'Unknown'),
            'permalink_url': info.get('uploader_url', ''),
            'avatar_url': info.get('thumbnail', '')
        }


def split_tags(tag_string):
    pattern = r'"[^"]*"|\S+'
    matches = re.findall(pattern, tag_string)
    tags = [tag.strip('"') for tag in matches]
    return tags


def fetchTrackWithYtDlp(track_url):
    ydl_opts: dict[str, Any] = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(track_url, download=False)
            if info and isinstance(info, dict):
                return YtDlpTrack(info)
    except Exception:
        pass
    return None


def fetchTrack(track_url):
    if track_url.startswith('https://on.soundcloud.com'):
        response = requests.get(track_url, allow_redirects=True)
        if response.status_code == 200:
            track_url = response.history[0].headers['location']
        else:
            raise Exception('Unable to fetch Soundcloud Mobile URL')
    try:
        api = SoundcloudAPI()
        track = api.resolve(track_url)
        return track
    except Exception as e:
        fallback_track = fetchTrackWithYtDlp(track_url)
        if fallback_track:
            return fallback_track
        raise


def getSoundcloudParts(url: str):
    soundcloudParts = {
        'embedPlatformType': 'soundcloud',
        'embedColour': 0xff5500
    }

    track = fetchTrack(remove_trailing_slash(url))

    if isinstance(track, (Track, YtDlpTrack)):
        if checkTrackTitle(track.title):
            setTrackTitle(track)
        artist = getTrackArtist(track)

        if artist.lower() in track.title.lower():
            soundcloudParts['title'] = track.title if artist.lower(
            ) == track.artist.lower() else f'{track.artist} - {track.title}'
        else:
            if artist == track.user.get('username'):
                artist = track.artist
            soundcloudParts['title'] = f'{artist} - {track.title}'

        if track.genre:
            soundcloudParts['Genre'] = f'`{track.genre}`'

        #Artwork
        soundcloudParts['thumbnailUrl'] = formatArtworkUrl(
            track.artwork_url if track.artwork_url else track.
            user['avatar_url'])

        #Duration
        soundcloudParts['Duration'] = formatMillisecondsToDurationString(
            track.duration)

        #Release date
        if track.created_at:
            soundcloudParts['Uploaded on'] = formatTimeToDisplay(
                track.created_at, '%Y-%m-%dT%H:%M:%SZ')

        #Likes
        if track.likes_count:
            soundcloudParts['Likes'] = f':orange_heart: {track.likes_count}'

        #Plays
        if track.playback_count:
            soundcloudParts['Plays'] = f':notes: {track.playback_count:,}'

        #Buy Link
        if track.purchase_url:
            buyLinkName = track.purchase_title or 'Buy/Stream'
            isDownload = any(word in buyLinkName.lower()
                             for word in ['download', 'free', 'dl'])
            soundcloudParts['Buy/Download Link'] = (
                f'{":arrow_down:" if isDownload else ":link:"} '
                f'[{buyLinkName}](<{track.purchase_url}>)')
        elif track.downloadable and track.has_downloads_left:
            soundcloudParts['description'] = (
                ':arrow_down: **Download button is on** :arrow_down:' +
                (f'[here](<{track.download_url}>)'
                 if track.download_url else ''))

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
            soundcloudParts['description'] = f'{track.track_count} track album'
            soundcloudParts['Artist'] = (f'[{track.user["username"]}]'
                                         f'({track.user["permalink_url"]})')
            trackStrings = []
            trackSummaryCharLength = 0
            maxDisplayableTracksReached = False
            for song in track.tracks:
                if not maxDisplayableTracksReached:
                    outputString = (
                        f'1. [{song.title}]({song.permalink_url}) '
                        f'{formatMillisecondsToDurationString(song.duration)}')
                    outputStringLength = len(outputString) + 1
                    if trackSummaryCharLength + outputStringLength <= 1000:
                        trackStrings.append(outputString)
                        trackSummaryCharLength += outputStringLength
                    else:
                        maxDisplayableTracksReached = True

            soundcloudParts['Tracks'] = '\n'.join(trackStrings)
            if len(trackStrings) != track.track_count:
                soundcloudParts['Tracks'] += (
                    f'\n...and {track.track_count - len(trackStrings)} more')
        else:
            soundcloudParts[
                'description'] = f'Playlist ({track.track_count} tracks)'

        #Artwork
        if track.artwork_url or track.track_count > 0:
            soundcloudParts['thumbnailUrl'] = formatArtworkUrl(
                track.artwork_url if track.artwork_url else track.tracks[0].
                artwork_url if track.tracks[0].artwork_url else track.
                tracks[0].user['avatar_url'])

        #Genre
        if track.genre:
            soundcloudParts['Genre'] = f'`{track.genre}`'

        #Duration
        soundcloudParts['Duration'] = formatMillisecondsToDurationString(
            track.duration)

        #Likes
        soundcloudParts['Likes'] = f':orange_heart: {track.likes_count}'

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
    return soundcloudParts


def checkTrackTitle(track_title):
    return '-' in track_title or '–' in track_title or '—' in track_title


def setTrackTitle(track: Union[Track, 'YtDlpTrack']):
    trackNameRegex = r"(.+?)\s[-—–]\s(.*)"
    fullTitle = f'{track.artist}-{track.title}' if track.artist != track.user.get(
        'username') else track.title
    match = re.match(trackNameRegex, fullTitle)
    if match:
        track.title = match.group(2)
        track.artist = match.group(1)


def getTrackArtist(track: Union[Track, 'YtDlpTrack']):
    user = track.user.get('username')
    if track.publisher_metadata:
        # metaComposer = track.publisher_metadata.get('writer_composer')
        metaArtist = track.publisher_metadata.get('artist')
        if metaArtist is not None:
            return metaArtist 
        # if metaArtist and user and metaArtist != user:
        #     return metaArtist
        # elif metaComposer:
        #     return metaComposer
        # elif metaArtist:
        #     return metaArtist
    return track.artist


def formatArtworkUrl(url: str):
    return url.replace('large', 't500x500')
