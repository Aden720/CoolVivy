import os
import re
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from general_utils import formatMillisecondsToDurationString, formatTimeToDisplay
from object_types.spotify_types import SpotifyAlbum, SpotifyPlaylist, SpotifyPlaylistTracks

spotifyClientId = os.getenv("SPOTIFY_CLIENT_ID")
spotifyClientSecret = os.getenv("SPOTIFY_CLIENT_SECRET")


def getSpotifyParts(embed):
    spotifyParts = {'embedPlatformType': 'spotify', 'embedColour': 0x1db954}

    try:
        #fetches the data from the spotify url
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=spotifyClientId, client_secret=spotifyClientSecret))

        if embed.url.startswith('https://open.spotify.com/track'):
            track = sp.track(embed.url)
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
                spotifyParts['Album'] = (f'[{album["name"]}](\
                {album["external_urls"]["spotify"]})')

            #title
            title = reformatTitle(title)
            spotifyParts['title'] = (f'{titleArtists} - {title}'
                                     if titleArtists else title)
        elif embed.url.startswith('https://open.spotify.com/album'):
            data = sp.album(embed.url)
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
                        f' `{formatMillisecondsToDurationString(track["duration_ms"])}`'
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
                spotifyParts['description'] = f'{album["total_tracks"]} \
                track album'

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

        elif embed.url.startswith('https://open.spotify.com/playlist'):
            data = sp.playlist(embed.url)
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
        print(f"Error occurred: {e}")
        #fallback method from embed
        attributes = ['Artist', 'Type', 'Released']
        parts = embed.description.split(' · ')
        if parts[1] == 'Single' or parts[1] == 'Album' or parts[1] == 'EP':
            attributes = ['Artist', 'Type', 'Released']
            if len(parts) > 3 and parts[1] != 'Single':
                parts[1] = f'{parts[1]} - {parts[3]}'  #Type - Track num
                parts.pop(3)
        elif parts[0] == 'Playlist':
            attributes = ['Artist', 'Type', 'Saves :green_heart:']
            parts[0], parts[1] = parts[1], parts[0]
            if len(parts) > 3:
                parts[1] = f'{parts[1]} - {parts[2]}'  #Playlist - num items
                parts.pop(2)
        else:
            attributes = ['Artist', 'Album', 'Type', 'Released']

        for index, attribute in enumerate(attributes):
            spotifyParts[f'{attribute}'] = parts[index]

        #remove album field because embed doesn't look great
        spotifyParts.pop('Album', None)

        artist_parts_comma = spotifyParts['Artist'].split(', ')
        if len(artist_parts_comma) > 1:
            spotifyParts['Artists'] = spotifyParts['Artist']
            spotifyParts.pop('Artist', None)

        # Reorder keys: 'Type' and 'Released' should follow 'Artists' or 'Artist'
        if 'Artists' in spotifyParts:
            order = ['Artists'
                     ] + [key for key in spotifyParts if key != 'Artists']
            spotifyParts = {
                key: spotifyParts[key]
                for key in order if key in spotifyParts
            }

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
