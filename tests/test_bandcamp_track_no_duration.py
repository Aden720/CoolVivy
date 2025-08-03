
import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from bandcamp_utils import Track


class TestBandcampTrackNoDuration(unittest.TestCase):

    def test_track_mapping_no_duration(self):
        # Arrange - Create mock pageData and trackData for a track with no duration
        pageData = {
            '@id': 'http://test.bandcamp.com/track/test-track',
            'name': 'Test Track',
            'keywords': ['tag1', 'tag2', 'tag3'],
            'image': 'http://test.com/image.jpg',
            'byArtist': {
                'name': 'Test Artist',
                '@id': 'http://test.bandcamp.com'
            },
            'datePublished': '01 Jan 2022 12:00:00 GMT',
            'inAlbum': {
                'name': 'Test Album',
                '@id': 'http://test.bandcamp.com/album/test-album',
                'numTracks': 10,
                'byArtist': {
                    'name': 'Test Artist',
                    '@id': 'http://test.bandcamp.com'
                }
            },
            'publisher': {
                'name': 'Test Artist',
                '@id': 'http://test.bandcamp.com'
            }
        }
        
        trackData = {
            'is_purchasable': True,
            'free_download': False,
            'price': 1.0,
            'currency': 'USD',
            'tracks': [{'duration': None}],  # No duration
            'release_date': 1640995200,  # timestamp for 2022-01-01
            'tags': [{'name': 'electronic'}, {'name': 'ambient'}]
        }
        
        track = Track(pageData, trackData)

        # Act
        parts = track.mapToParts()

        # Assert
        # Verify that Duration field is not included when duration is None
        self.assertNotIn('Duration', parts)
        
        # Verify other fields are still present
        self.assertEqual(parts['title'], 'Test Artist - Test Track')
        self.assertEqual(parts['Price'], '`$1.00`')
        self.assertEqual(parts['Artist'], '[Test Artist](http://test.bandcamp.com)')
        self.assertEqual(parts['Album'], '[Test Album](http://test.bandcamp.com/album/test-album)')
        self.assertEqual(parts['Tags'], '`electronic`, `ambient`')
        
    def test_track_mapping_zero_duration(self):
        # Arrange - Create mock data for a track with zero duration
        pageData = {
            '@id': 'http://test.bandcamp.com/track/test-track',
            'name': 'Test Track',
            'image': 'http://test.com/image.jpg',
            'byArtist': {
                'name': 'Test Artist',
                '@id': 'http://test.bandcamp.com'
            },
            'datePublished': '01 Jan 2022 12:00:00 GMT',
            'inAlbum': {
                'name': 'Test Album',
                '@id': 'http://test.bandcamp.com/album/test-album',
                'numTracks': 10,
                'byArtist': {
                    'name': 'Test Artist',
                    '@id': 'http://test.bandcamp.com'
                }
            },
            'publisher': {
                'name': 'Test Artist',
                '@id': 'http://test.bandcamp.com'
            }
        }
        
        trackData = {
            'is_purchasable': True,
            'free_download': False,
            'price': 1.0,
            'currency': 'USD',
            'tracks': [{'duration': 0}],  # Zero duration
            'release_date': 1640995200,
            'tags': []
        }
        
        track = Track(pageData, trackData)

        # Act
        parts = track.mapToParts()

        # Assert
        # Verify that Duration field is not included when duration is 0
        self.assertNotIn('Duration', parts)
        
        # Verify other fields are still present
        self.assertEqual(parts['title'], 'Test Artist - Test Track')
        self.assertEqual(parts['Price'], '`$1.00`')


if __name__ == '__main__':
    unittest.main()
