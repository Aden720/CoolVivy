from unittest.mock import MagicMock

from bandcamp_utils import Track


class MockTrack(Track):

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
        self.thumbnail = None
        self.free_download = False
