from unittest.mock import MagicMock


class MockTrack:

    def __init__(self,
                 title='Test Track',
                 artist='Test Artist',
                 url='http://test.com'):
        self.title = title
        self.artist = {'name': artist, 'url': url}
        self.publisher = {
            'name': 'Test Publisher',
            'url': 'http://publisher.com'
        }
        self.album = {'name': 'Test Album', 'url': 'http://album.com'}
        self.trackUrl = 'http://track.com'
        self.duration = 180
        self.release_date = 1609459200
        self.is_purchasable = True
        self.price = 7.00
        self.currency = 'USD'
        self.tags = ['tag1', 'tag2']


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
