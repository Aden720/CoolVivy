import unittest
from unittest.mock import patch

from mockData.bandcamp_mock_scenarios import (
    MockTrack,
    setupAlbumEmbed,
    setupBasicEmbed,
    setupDiscographyEmbed,
)

from bandcamp_utils import getBandcampParts, getPartsFromEmbed


class TestBandcampUtils(unittest.TestCase):

    def test_getPartsFromEmbed_track(self):
        # Arrange
        embed = setupBasicEmbed()

        # Act
        result = getPartsFromEmbed(embed)

        # Assert
        self.assertEqual(result['title'], 'Artist Name - Song Title')
        self.assertEqual(result['Artist'],
                         '[Artist Name](https://artist.bandcamp.com)')
        self.assertEqual(result['Album'], 'Album Name')
        self.assertNotIn('Channel', result)

    def test_getPartsFromEmbed_track_with_hyphen(self):
        # Arrange
        embed = setupBasicEmbed()
        embed.title = 'Featured Artist - Song Title, by Artist Name'

        # Act
        result = getPartsFromEmbed(embed)

        # Assert
        self.assertEqual(result['title'], 'Featured Artist - Song Title')
        self.assertEqual(result['Artist'], 'Featured Artist')
        self.assertEqual(result['Channel'],
                         '[Artist Name](https://artist.bandcamp.com)')

    def test_getPartsFromEmbed_track_with_ampersand(self):
        # Arrange
        embed = setupBasicEmbed()
        embed.title = 'Artist One & Artist Two - Song Title, by Channel Name'
        embed.provider.name = 'Channel Name'

        # Act
        result = getPartsFromEmbed(embed)

        # Assert
        self.assertEqual(result['title'],
                         'Artist One & Artist Two - Song Title')
        self.assertEqual(result['Artists'], 'Artist One & Artist Two')
        self.assertEqual(result['Channel'],
                         '[Channel Name](https://artist.bandcamp.com)')

    def test_getPartsFromEmbed_track_with_multiple_artists(self):
        # Arrange
        embed = setupBasicEmbed()
        embed.title = 'Artist One, Artist Two - Song Title, by Channel Name'
        embed.provider.name = 'Channel Name'

        # Act
        result = getPartsFromEmbed(embed)

        # Assert
        self.assertEqual(result['title'],
                         'Artist One, Artist Two - Song Title')
        self.assertEqual(result['Artists'], 'Artist One, Artist Two')
        self.assertEqual(result['Channel'],
                         '[Channel Name](https://artist.bandcamp.com)')

    def test_getPartsFromEmbed_album(self):
        # Arrange
        embed = setupAlbumEmbed()

        # Act
        result = getPartsFromEmbed(embed)

        # Assert
        self.assertEqual(result['title'], 'Artist Name - Album Title')
        self.assertEqual(result['Artist'],
                         '[Artist Name](https://artist.bandcamp.com)')

    def test_getPartsFromEmbed_various_artists(self):
        # Arrange
        embed = setupBasicEmbed()
        embed.title = 'Compilation Title, by Various Artists'

        # Act

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
                         '`:arrow_down: [Free Download](http://track.com)`')

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

    def test_getBandcampParts_discography(self):
        # Arrange
        embed = setupDiscographyEmbed()

        # Act
        result = getBandcampParts(embed)

        # Assert
        self.assertEqual(result['embedPlatformType'], 'bandcamp')
        self.assertEqual(result['embedColour'], 0x1da0c3)
        self.assertEqual(result['title'], 'Artist Name')
        self.assertEqual(result['description'], 'Discography')

    @patch('bandcamp_utils.BandcampScraper')
    def test_getBandcampParts_fallback(self, mock_scraper):
        # Arrange
        embed = setupBasicEmbed()
        mock_scraper.side_effect = Exception('Test exception')

        # Act
        result = getBandcampParts(embed)

        # Assert
        self.assertEqual(result['embedPlatformType'], 'bandcamp')
        self.assertEqual(result['embedColour'], 0x1da0c3)
        self.assertEqual(result['title'], 'Artist Name - Song Title')
