
from unittest.mock import MagicMock


def create_base_embed():
    embed = MagicMock()
    embed.url = ''
    embed.title = ''
    embed.provider = MagicMock()
    embed.provider.name = 'Artist Name'
    embed.provider.url = 'https://artist.bandcamp.com'
    return embed


def setupBasicEmbed():
    embed = create_base_embed()
    embed.url = 'https://artist.bandcamp.com/track/song-title'
    embed.title = 'Song Title, by Artist Name'
    embed.description = 'from the album Album Name'
    return embed


def setupAlbumEmbed():
    embed = create_base_embed()
    embed.url = 'https://artist.bandcamp.com/album/album-title'
    embed.title = 'Album Title, by Artist Name'
    return embed


def setupDiscographyEmbed():
    embed = create_base_embed()
    embed.url = 'https://artist.bandcamp.com/music'
    return embed
