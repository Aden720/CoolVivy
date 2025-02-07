
import unittest
from unittest.mock import patch

from mockData.bandcamp_mock_scenarios import (
    setupBasicEmbed,
    setupAlbumEmbed,
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
        self.assertEqual(result['Artist'], '[Artist Name](https://artist.bandcamp.com)')
        self.assertEqual(result['Album'], 'Album Name')

    def test_getPartsFromEmbed_album(self):
        # Arrange
        embed = setupAlbumEmbed()

        # Act
        result = getPartsFromEmbed(embed)

        # Assert
        self.assertEqual(result['title'], 'Artist Name - Album Title')
        self.assertEqual(result['Artist'], '[Artist Name](https://artist.bandcamp.com)')

    def test_getPartsFromEmbed_various_artists(self):
        # Arrange
        embed = setupBasicEmbed()
        embed.title = 'Compilation Title, by Various Artists'

        # Act
        result = getPartsFromEmbed(embed)

        # Assert
        self.assertEqual(result['title'], 'Compilation Title')
        self.assertEqual(result['Artist'], 'Various Artists')

    @patch('bandcamp_utils.BandcampScraper')
    def test_getBandcampParts_discography(self, mock_scraper):
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
