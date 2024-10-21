import os

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

spotifyClientId = os.getenv("SPOTIFY_CLIENT_ID")
spotifyClientSecret = os.getenv("SPOTIFY_CLIENT_SECRET")


def getSpotifyParts(embed):
    spotifyParts = {'embedPlatformType': 'spotify', 'embedColour': 0x1db954}

    try:
        raise Exception('bypassing until mapping is complete')
        #fetches the data from the spotify url
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=spotifyClientId, client_secret=spotifyClientSecret))

        if embed.url.startswith('https://open.spotify.com/track'):
            track = sp.track(embed.url)
            spotifyParts['Artist'] = track['artists'][0]['name']
            spotifyParts['Type'] = 'Track'
            spotifyParts['Duration'] = track['duration_ms']
            spotifyParts['Released'] = track['album']['release_date'][:4]
        elif embed.url.startswith('https://open.spotify.com/album'):
            album = sp.album(embed.url)
        elif embed.url.startswith('https://open.spotify.com/playlist'):
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
