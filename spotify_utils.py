def getSpotifyParts(embed):
    spotifyParts = {'embedPlatformType': 'spotify'}
    attributes = ['Artist', 'Type', 'Released']
    parts = embed.description.split(' · ')
    if parts[1] == 'Single' or parts[1] == 'Album':
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
        attributes = ['Artist', 'title', 'Type', 'Released']

    for index, attribute in enumerate(attributes):
        spotifyParts[f'{attribute}'] = parts[index]

    artist_parts_comma = spotifyParts['Artist'].split(', ')
    if len(artist_parts_comma) > 1:
        spotifyParts['Artists'] = spotifyParts['Artist']
        spotifyParts.pop('Artist', None)

    # Reorder keys: 'Type' and 'Released' should follow 'Artists' or 'Artist'
    if 'Artists' in spotifyParts:
        order = ['Artists'] + [key for key in spotifyParts if key != 'Artists']
        spotifyParts = {
            key: spotifyParts[key]
            for key in order if key in spotifyParts
        }

    return spotifyParts
