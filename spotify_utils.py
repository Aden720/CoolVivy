import logging
import os
import re
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from general_utils import formatMillisecondsToDurationString, formatTimeToDisplay
from object_types.spotify_types import (
    SpotifyAlbum,
    SpotifyPlaylist,
    SpotifyPlaylistTracks,
)

logger = logging.getLogger(__name__)

spotifyClientId = os.getenv("SPOTIFY_CLIENT_ID")
spotifyClientSecret = os.getenv("SPOTIFY_CLIENT_SECRET")


def getSpotifyParts(url: str):
    spotifyParts = {'embedPlatformType': 'spotify', 'embedColour': 0x1db954}

    try:
        #fetches the data from the spotify url
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=spotifyClientId, client_secret=spotifyClientSecret))

        if '/track/' in url and 'open.spotify.com' in url:
            track = sp.track(url)
            if not track:
                raise Exception('Spotify track data not found')

            #aliases
            title = track['name']
            artists = track['artists']
            album = track['album']

            #duration
            spotifyParts['Duration'] = (formatMillisecondsToDurationString(
                track["duration_ms"]))

            #Released on
            spotifyParts['Released'] = getReleaseDateString(album)

            #thumbnail
            if len(album['images']) > 0:
                spotifyParts['thumbnailUrl'] = album['images'][0]['url']

            #artist
            artistString = getFormattedArtistString(artists)
            titleArtists = getFormattedTitleArtistString(artists, title)
            if len(artists) > 1:
                spotifyParts['Artists'] = artistString
            else:
                spotifyParts['Artist'] = artistString
            # spotifyParts['Type'] = 'Track'

            #album
            if album.get('total_tracks') > 1:
                spotifyParts['Album'] = (f'[{album["name"]}]({album["external_urls"]["spotify"]})')

            #title
            title = reformatTitle(title)
            spotifyParts['title'] = (f'{titleArtists} - {title}'
                                     if titleArtists else title)
        elif '/album/' in url and 'open.spotify.com' in url:
            data = sp.album(url)
            if not data:
                raise Exception('Spotify album data not found')
            album: SpotifyAlbum = data
            #aliases
            title = album['name']
            artists = album['artists']
            tracks = album['tracks']['items']
            totalTracks = album['total_tracks']

            artistString = getFormattedArtistString(artists)
            titleArtists = getFormattedTitleArtistString(artists, title)

            trackStrings = []
            trackSummaryCharLength = 0
            totalDuration = 0
            maxDisplayableTracksReached = False
            for track in tracks:
                totalDuration += track['duration_ms']
                if not maxDisplayableTracksReached:
                    trackTitle = reformatTitle(track['name'])
                    trackArtists = getFormattedTitleArtistString(
                        track['artists'], trackTitle)
                    trackString = (
                        f'{track["track_number"]}. ' +
                        (f'[{trackArtists} - {trackTitle}]' if trackArtists and
                         trackArtists != titleArtists else f'[{trackTitle}]') +
                        f'({track["external_urls"]["spotify"]})' +
                        f' {formatMillisecondsToDurationString(track["duration_ms"])}'
                    )
                    trackStringLength = len(trackString) + 1
                    if trackSummaryCharLength + trackStringLength <= 1000:
                        trackStrings.append(trackString)
                        trackSummaryCharLength += trackStringLength
                    else:
                        maxDisplayableTracksReached = True

            spotifyParts['Duration'] = (
                formatMillisecondsToDurationString(totalDuration))

            #Artist
            if len(artists) > 1:
                spotifyParts['Artists'] = artistString
            elif artists[0]['name'] == 'Various Artists':
                spotifyParts['Artists'] = 'Various Artists'
            else:
                spotifyParts['Artist'] = artistString

            #Label
            if album.get('label'):
                spotifyParts['Label'] = album['label']

            #thumbnail
            if len(album['images']) > 0:
                spotifyParts['thumbnailUrl'] = album['images'][0]['url']

            #Description
            if totalTracks > 1:
                spotifyParts['description'] = f'{album["total_tracks"]} track album'

            else:
                spotifyParts['Duration'] = (formatMillisecondsToDurationString(
                    tracks[0]["duration_ms"]))

            #Released on
            spotifyParts['Released'] = getReleaseDateString(album)

            if totalTracks > 1:
                spotifyParts['Tracks'] = '\n'.join(trackStrings)
                if len(trackStrings) != totalTracks:
                    spotifyParts[
                        'Tracks'] += f'\n...and {totalTracks - len(trackStrings)} more'

            #title
            spotifyParts['title'] = (
                f'{titleArtists} - {title}' if titleArtists
                and titleArtists != 'Various Artists' else title)

        elif '/playlist/' in url and 'open.spotify.com' in url:
            data = sp.playlist(url)
            if not data:
                raise Exception('Spotify playlist data not found')
            playlist: SpotifyPlaylist = data

            #aliases
            tracks = playlist['tracks']['items']
            totalTracks = playlist['tracks']['total']

            #title
            spotifyParts['title'] = playlist['name']

            #read in paginated track data
            trackStrings = []
            trackSummaryCharLength = 0
            totalDuration = 0
            maxDisplayableTracksReached = False
            for trackEntry in tracks:
                track = trackEntry['track']
                totalDuration += track['duration_ms']
                if not maxDisplayableTracksReached:
                    trackTitle = reformatTitle(track['name'])
                    trackArtists = getFormattedTitleArtistString(
                        track['artists'], trackTitle)
                    trackString = (
                        '1. ' + (f'[{trackArtists} - {trackTitle}]'
                                 if trackArtists else f'[{trackTitle}]') +
                        f'({track["external_urls"]["spotify"]})' +
                        f' `{formatMillisecondsToDurationString(track["duration_ms"])}`'
                    )
                    trackStringLength = len(trackString) + 1
                    if trackSummaryCharLength + trackStringLength <= 1000:
                        trackStrings.append(trackString)
                        trackSummaryCharLength += trackStringLength
                    else:
                        maxDisplayableTracksReached = True

            current_track_page: Optional[SpotifyPlaylistTracks] = playlist[
                'tracks']
            while current_track_page and current_track_page['next']:
                current_track_page = sp.next(current_track_page)
                if current_track_page:
                    for trackEntry in current_track_page['items']:
                        totalDuration += trackEntry['track']['duration_ms']

            #duration
            spotifyParts['Duration'] = (
                formatMillisecondsToDurationString(totalDuration))

            #creator/owner
            spotifyParts['Created by'] = (
                f'[{playlist["owner"]["display_name"]}]({playlist["owner"]["external_urls"]["spotify"]})'
            )
            spotifyParts['Saves'] = f'`{playlist["followers"]["total"]}`'

            #thumbnail
            if len(playlist['images']) > 0:
                spotifyParts['thumbnailUrl'] = playlist['images'][0]['url']

            #description
            if playlist.get('description'):
                spotifyParts['Description'] = playlist['description']
            spotifyParts['description'] = (f'Playlist ({totalTracks} songs)')

            #tracks
            spotifyParts['Tracks'] = '\n'.join(trackStrings)
            if len(trackStrings) != totalTracks:
                spotifyParts['Tracks'] += (
                    f'\n...and {totalTracks - len(trackStrings)} more')

    except Exception as e:
        logger.error(f"Error occurred while fetching Spotify details: {e}")
        #fallback method from embed

    return spotifyParts


def getReleaseDateString(album):
    releaseDate = album['release_date']
    releaseDateFormat = album['release_date_precision']
    if releaseDateFormat == 'day':
        releaseDateString = formatTimeToDisplay(releaseDate, '%Y-%m-%d')
    elif releaseDateFormat == 'month':
        releaseDateString = formatTimeToDisplay(releaseDate, '%Y-%m', '%B %Y')
    else:
        releaseDateString = releaseDate
    return releaseDateString


def getFormattedArtistString(artists):
    return ', '.join([
        f'[{artist["name"]}]({artist["external_urls"]["spotify"]})'
        for artist in artists
    ])


def getFormattedTitleArtistString(artists, title):
    return ', '.join(
        [artist['name'] for artist in artists if artist['name'] not in title])


def reformatTitle(title):
    remixRegex = r"(.+?)\s[-–]\s(.*?(Remix|Mix|Edit).*)"
    if re.match(remixRegex, title):
        title = re.sub(remixRegex, r'\1 (\2)', title)
    return title
