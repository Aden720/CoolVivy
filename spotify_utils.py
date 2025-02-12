import os
import re

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from general_utils import formatMillisecondsToDurationString, formatTimeToDisplay

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
            releaseDate = album['release_date']
            releaseDateFormat = album['release_date_precision']

            #duration
            spotifyParts['Duration'] = (formatMillisecondsToDurationString(
                track["duration_ms"]))

            #Released on
            if releaseDateFormat == 'day':
                releaseDateString = formatTimeToDisplay(
                    releaseDate, '%Y-%m-%d')
            elif releaseDateFormat == 'month':
                releaseDateString = formatTimeToDisplay(
                    releaseDate, '%Y-%m', '%B %Y')
            else:
                releaseDateString = releaseDate
            spotifyParts['Released'] = releaseDateString

            #thumbnail
            if len(album['images']) > 0:
                spotifyParts['thumbnailUrl'] = album['images'][0]['url']

            #artist
            artistString = ', '.join([
                f'[{artist["name"]}]({artist["external_urls"]["spotify"]})'
                for artist in artists
            ])
            titleArtists = ', '.join([
                artist['name'] for artist in artists
                if artist['name'] not in title
            ])
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
            remixRegex = r"(.+?)\s[-–]\s(.*?(Remix|Mix|Edit).*)"
            if re.match(remixRegex, title):
                title = re.sub(remixRegex, r'\1 (\2)', title)
            spotifyParts['title'] = (f'{titleArtists} - {title}'
                                     if titleArtists else title)
        elif embed.url.startswith('https://open.spotify.com/album'):
            raise Exception('bypassing until mapping is complete')
            album = sp.album(embed.url)
        elif embed.url.startswith('https://open.spotify.com/playlist'):
            raise Exception('bypassing until mapping is complete')
            playlist = sp.playlist(embed.url)
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
