import unittest

from bandcamp_utils import Track


class TestTrackMapping(unittest.TestCase):

    def setUp(self):
        """Set up base test data for Track initialization"""
        self.base_track_data = {
            'is_purchasable': True,
            'free_download': False,
            'price': 7.00,
            'currency': 'USD',
            'tracks': [{
                'duration': 180
            }],
            'release_date': 1609459200,
            'tags': [{
                'name': 'tag1'
            }, {
                'name': 'tag2'
            }]
        }

    def create_base_page_data(
            self,
            track_name='Test Track',
            track_artist_name='Track Artist',
            track_artist_url='https://trackartist.bandcamp.com',
            album_name='Test Album',
            publisher_name='Publisher Name'):
        """Create base page data with customizable values"""
        return {
            '@id': 'https://artist.bandcamp.com/track/test-track',
            'name': track_name,
            'image': 'https://example.com/image.jpg',
            'byArtist': {
                'name': track_artist_name,
                '@id': track_artist_url
            },
            'inAlbum': {
                'name': album_name,
                '@id': 'https://artist.bandcamp.com/album/test-album',
                'numTracks': 10
            },
            'publisher': {
                'name': publisher_name,
                '@id': 'https://publisher.bandcamp.com'
            }
        }

    def test_track_mapping_no_album_artist(self):
        """Test track mapping when album has no byArtist field"""
        page_data = self.create_base_page_data()
        # Remove byArtist from inAlbum
        page_data['inAlbum'] = {
            'name': 'Test Album',
            '@id': 'https://artist.bandcamp.com/album/test-album',
            'numTracks': 10
        }

        track = Track(page_data, self.base_track_data)

        self.assertEqual(track.artist['name'], 'Track Artist')
        self.assertEqual(track.artist['url'],
                         'https://trackartist.bandcamp.com')

    def test_track_mapping_album_artist_same_as_track_artist(self):
        """Test track mapping when album artist is same as track artist"""
        page_data = self.create_base_page_data()
        page_data['inAlbum']['byArtist'] = {
            'name': 'Track Artist',
            '@id': 'https://trackartist.bandcamp.com'
        }

        track = Track(page_data, self.base_track_data)

        self.assertEqual(track.artist['name'], 'Track Artist')
        self.assertEqual(track.artist['url'],
                         'https://trackartist.bandcamp.com')

    def test_track_mapping_album_artist_different_from_track_artist(self):
        """Test track mapping when album artist is different from track artist (line 44 case)"""
        page_data = self.create_base_page_data()
        page_data['inAlbum']['byArtist'] = {
            'name': 'Album Artist',
            '@id': 'https://albumartist.bandcamp.com'
        }

        track = Track(page_data, self.base_track_data)

        # Should use album artist instead of track artist
        self.assertEqual(track.artist['name'], 'Album Artist')
        self.assertEqual(track.artist['url'],
                         'https://albumartist.bandcamp.com')

    def test_track_mapping_album_artist_various_artists(self):
        """Test track mapping when album artist is 'Various' (should keep track artist)"""
        page_data = self.create_base_page_data()
        page_data['inAlbum']['byArtist'] = {
            'name': 'Various',
            '@id': 'https://various.bandcamp.com'
        }

        track = Track(page_data, self.base_track_data)

        # Should keep original track artist when album artist is 'Various'
        self.assertEqual(track.artist['name'], 'Track Artist')
        self.assertEqual(track.artist['url'],
                         'https://trackartist.bandcamp.com')

    def test_track_mapping_album_artist_various_artists_full(self):
        """Test track mapping when album artist is 'Various Artists' (should keep track artist)"""
        page_data = self.create_base_page_data()
        page_data['inAlbum']['byArtist'] = {
            'name': 'Various Artists',
            '@id': 'https://various.bandcamp.com'
        }

        track = Track(page_data, self.base_track_data)

        # Should keep original track artist when album artist is 'Various Artists'
        self.assertEqual(track.artist['name'], 'Track Artist')
        self.assertEqual(track.artist['url'],
                         'https://trackartist.bandcamp.com')

    def test_track_mapping_album_artist_no_url(self):
        """Test track mapping when album artist has no URL"""
        page_data = self.create_base_page_data()
        page_data['inAlbum']['byArtist'] = {
            'name': 'Album Artist'
            # No '@id' field
        }

        track = Track(page_data, self.base_track_data)

        # Should use album artist but with None URL
        self.assertEqual(track.artist['name'], 'Album Artist')
        self.assertIsNone(track.artist['url'])

    def test_track_mapping_album_artist_empty_name(self):
        """Test track mapping when album artist has empty name"""
        page_data = self.create_base_page_data()
        page_data['inAlbum']['byArtist'] = {
            'name': '',
            '@id': 'https://empty.bandcamp.com'
        }

        track = Track(page_data, self.base_track_data)

        # Should keep original track artist when album artist name is empty
        self.assertEqual(track.artist['name'], 'Track Artist')
        self.assertEqual(track.artist['url'],
                         'https://trackartist.bandcamp.com')

    def test_track_mapping_album_artist_none_name(self):
        """Test track mapping when album artist name is None"""
        page_data = self.create_base_page_data()
        page_data['inAlbum']['byArtist'] = {
            'name': None,
            '@id': 'https://none.bandcamp.com'
        }

        track = Track(page_data, self.base_track_data)

        # Should keep original track artist when album artist name is None
        self.assertEqual(track.artist['name'], 'Track Artist')
        self.assertEqual(track.artist['url'],
                         'https://trackartist.bandcamp.com')

    def test_track_title_modification_when_artist_in_title(self):
        """Test the logic at when artist name is in the track title"""
        # Arrange
        page_data = self.create_base_page_data(
            track_name='Test Artist - Test Track',  # Artist name is in the title
            track_artist_name='Test Artist',
            track_artist_url='https://testartist.bandcamp.com',
            publisher_name='Publisher Name'  # Different from artist
        )

        # Act
        track = Track(page_data, self.base_track_data)

        # Assert - The title should be modified to remove the artist name
        self.assertEqual(track.title,
                         'Test Track')  # Artist name removed from title
        self.assertEqual(track.artist['name'], 'Test Artist')
        self.assertEqual(track.artist['url'],
                         'https://testartist.bandcamp.com')


if __name__ == '__main__':
    unittest.main()
