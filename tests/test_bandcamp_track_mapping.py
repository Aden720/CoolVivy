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
        """
        Test track mapping when album artist is different from track artist
        (line 44 case)
        """
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
        """
        Test track mapping when album artist is 'Various'
        (should keep track artist)
        """
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
        """
        Test track mapping when album artist is 'Various Artists'
        (should keep track artist)
        """
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

    def test_tags_mapping_from_page_data_keywords(self):
        """Test tags mapping from page data keywords (excludes first and last)"""
        # Arrange
        page_data = self.create_base_page_data()
        page_data['keywords'] = [
            'first', 'electronic', 'ambient', 'experimental', 'last'
        ]

        track_data = self.base_track_data.copy()
        del track_data['tags']  # Remove track data tags to test only page data

        # Act
        track = Track(page_data, track_data)

        # Assert - Should have tags from middle of keywords array
        self.assertEqual(track.tags, ['electronic', 'ambient', 'experimental'])

    def test_tags_mapping_from_page_data_keywords_short_array(self):
        """Test tags mapping when keywords array has 3 or fewer items"""
        # Arrange
        page_data = self.create_base_page_data()
        page_data['keywords'] = ['first', 'middle', 'last']  # Only 3 items

        track_data = self.base_track_data.copy()
        del track_data['tags']  # Remove track data tags

        # Act
        track = Track(page_data, track_data)

        # Assert - Should not have tags from page data when array is too short
        self.assertFalse(hasattr(track, 'tags'))

    def test_tags_mapping_from_page_data_no_keywords(self):
        """Test tags mapping when no keywords in page data"""
        # Arrange
        page_data = self.create_base_page_data()
        # No keywords field in page data

        track_data = self.base_track_data.copy()
        del track_data['tags']  # Remove track data tags

        # Act
        track = Track(page_data, track_data)

        # Assert - Should not have tags
        self.assertFalse(hasattr(track, 'tags'))

    def test_tags_mapping_from_track_data(self):
        """Test tags mapping from track data API response"""
        # Arrange
        page_data = self.create_base_page_data()
        # No keywords in page data

        track_data = self.base_track_data.copy()
        track_data['tags'] = [{
            'name': 'electronic'
        }, {
            'name': 'ambient'
        }, {
            'name': 'experimental'
        }]

        # Act
        track = Track(page_data, track_data)

        # Assert - Should have tags from track data
        expected_tags = ['electronic', 'ambient', 'experimental']
        self.assertEqual(list(track.tags), expected_tags)

    def test_tags_mapping_from_track_data_empty_tags(self):
        """Test tags mapping when track data has empty tags array"""
        # Arrange
        page_data = self.create_base_page_data()

        track_data = self.base_track_data.copy()
        track_data['tags'] = []  # Empty tags array

        # Act
        track = Track(page_data, track_data)

        self.assertFalse(hasattr(track, 'tags'))

    def test_tags_mapping_track_data_overrides_page_data(self):
        """Test that track data tags override page data keywords when both exist"""
        # Arrange
        page_data = self.create_base_page_data()
        page_data['keywords'] = ['first', 'page_tag1', 'page_tag2', 'last']

        track_data = self.base_track_data.copy()
        track_data['tags'] = [{'name': 'track_tag1'}, {'name': 'track_tag2'}]

        # Act
        track = Track(page_data, track_data)

        # Assert - Should use track data tags, not page data keywords
        expected_tags = ['track_tag1', 'track_tag2']
        self.assertEqual(list(track.tags), expected_tags)

    def test_tags_mapping_no_track_data(self):
        """Test tags mapping when track data is None"""
        # Arrange
        page_data = self.create_base_page_data()
        page_data['keywords'] = ['first', 'electronic', 'ambient', 'last']

        # Act
        track = Track(page_data, None)  # No track data

        # Assert - Should use tags from page data
        self.assertEqual(track.tags, ['electronic', 'ambient'])

    def test_tags_mapping_track_data_no_tags_field(self):
        """Test tags mapping when track data exists but has no tags field"""
        # Arrange
        page_data = self.create_base_page_data()
        page_data['keywords'] = ['first', 'electronic', 'ambient', 'last']

        track_data = self.base_track_data.copy()
        del track_data['tags']  # Remove tags field entirely

        # Act
        track = Track(page_data, track_data)

        # Assert - Should use tags from page data
        self.assertEqual(track.tags, ['electronic', 'ambient'])


if __name__ == '__main__':
    unittest.main()
