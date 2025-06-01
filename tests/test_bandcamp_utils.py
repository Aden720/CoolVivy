import unittest

from mockData.bandcamp_mock_scenarios import MockTrack


class TestBandcampUtils(unittest.TestCase):

    def test_track_mapping(self):
        # Arrange
        track = MockTrack()

        # Act
        parts = track.mapToParts()

        # Assert
        self.assertEqual(parts['title'], 'Test Artist - Test Track')
        self.assertEqual(parts['Duration'], '`3:00`')
        self.assertEqual(parts['Price'], '`$7.00`')
        self.assertEqual(parts['Artist'], '[Test Artist](http://test.com)')
        self.assertEqual(parts['Album'], '[Test Album](http://album.com)')
        self.assertEqual(parts['Tags'], '`tag1`, `tag2`')

    def test_track_mapping_free_download(self):
        # Arrange
        track = MockTrack()
        track.is_purchasable = False
        track.free_download = True

        # Act
        parts = track.mapToParts()

        # Assert
        self.assertEqual(parts['Price'],
                         ':arrow_down: [Free Download](http://track.com)')

    def test_track_with_different_publisher(self):
        # Arrange
        track = MockTrack()
        track.publisher['name'] = 'Different Publisher'

        # Act
        parts = track.mapToParts()

        # Assert
        self.assertTrue('Channel' in parts)
        self.assertEqual(parts['Channel'],
                         '[Different Publisher](http://publisher.com)')

    def test_track_with_multiple_artists(self):
        # Arrange
        track = MockTrack()
        track.artist = {
            'name': 'Artist One, Artist Two',
            'url': 'http://test.com'
        }

        # Act
        parts = track.mapToParts()

        # Assert
        self.assertEqual(parts['title'], 'Artist One, Artist Two - Test Track')
        self.assertIn('Artists', parts)
        self.assertEqual(parts['Artists'],
                         '[Artist One, Artist Two](http://test.com)')
        self.assertNotIn('Artist', parts)

    def test_track_with_multiple_artists_various_artists(self):
        # Arrange
        track = MockTrack()
        track.artist = {'name': 'Various Artists', 'url': 'http://test.com'}

        # Act
        parts = track.mapToParts()

        # Assert
        self.assertEqual(parts['title'], 'Test Track')
        self.assertIn('Artists', parts)
        self.assertEqual(parts['Artists'],
                         '[Various Artists](http://test.com)')
        self.assertNotIn('Artist', parts)

    def test_track_artist_in_title(self):
        # Arrange
        track = MockTrack()
        track.title = 'Test Track (Test Artist - Edit)'

        # Act
        parts = track.mapToParts()

        # Assert
        self.assertEqual(parts['title'], 'Test Track (Test Artist - Edit)')
        self.assertEqual(parts['Artist'], '[Test Artist](http://test.com)')
