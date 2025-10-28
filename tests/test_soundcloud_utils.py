# test_soundcloud_utils.py
import unittest
from unittest.mock import MagicMock, patch

from mockData.soundcloud_mock_scenarios import (
    setupBasicAlbum,
    setupBasicPlaylist,
    setupBasicTrack,
    setupBasicTrackWithBuyLinkBuy,
    setupBasicTrackWithBuyLinkDownload,
    setupBasicTrackWithDirectDownloadEnabled,
)
from sclib import Track

from soundcloud_utils import fetchTrack, getSoundcloudParts, split_tags


class TestSoundcloudUtils(unittest.TestCase):

    def test_split_tags(self):
        self.assertEqual(split_tags('Techno'), ['Techno'])

        self.assertEqual(split_tags('"Piano House"'), ['Piano House'])

        self.assertEqual(
            split_tags('Hardgroove Techno Dance Rave Edit Remix Rap '
                       '"Public Enemy" 90s CLEAR Raw'),
            [
                'Hardgroove', 'Techno', 'Dance', 'Rave', 'Edit', 'Remix',
                'Rap', 'Public Enemy', '90s', 'CLEAR', 'Raw'
            ])

    @patch('soundcloud_utils.requests.get')
    @patch('soundcloud_utils.SoundcloudAPI')
    def test_fetchTrack_http_mock_mobile(self, mock_soundcloud_api,
                                         mock_requests_get):
        # Simulate the HTTP response from the initial SoundCloud URL
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.history = [
            MagicMock(
                headers={'location': 'https://soundcloud.com/resolved-url'})
        ]
        mock_requests_get.return_value = mock_response
        # Mock the SoundcloudAPI resolve method to return a track
        mock_track = setupBasicTrack()
        mock_soundcloud_api.return_value.resolve.return_value = mock_track
        # URL to test
        mock_track_url = "https://on.soundcloud.com/someTrack"
        # Call the fetchTrack function
        result = fetchTrack(mock_track_url)
        # Assertions
        if isinstance(result, Track):
            self.assertEqual(result.artist, 'Mock Artist')
            self.assertEqual(result.title, 'Mock Track Title')
            mock_requests_get.assert_called_once_with(mock_track_url, allow_redirects=True)
            mock_soundcloud_api.return_value.resolve.assert_called_once_with(
                'https://soundcloud.com/resolved-url')
        else:
            self.fail("This test is intentionally failing.")

    @patch('soundcloud_utils.SoundcloudAPI')
    def test_fetchTrack_standard_url(self, mock_soundcloud_api):
        # Mobile URL normalization is now handled in general_utils.py
        # This test verifies that fetchTrack works with standard URLs
        mock_track = setupBasicTrack()
        mock_soundcloud_api.return_value.resolve.return_value = mock_track
        # URL to test - standard format after normalization
        mock_track_url = 'https://soundcloud.com/mosscaofficial/wax-motif-taiki-nulight-w-scrufizzer-skank-n-flex-mossca-flipexclusive'
        # Call the fetchTrack function
        result = fetchTrack(mock_track_url)
        # Assertions
        if isinstance(result, Track):
            self.assertEqual(result.artist, 'Mock Artist')
            self.assertEqual(result.title, 'Mock Track Title')
            # Standard URLs go directly to API resolve, no HTTP request needed
            mock_soundcloud_api.return_value.resolve.assert_called_once_with(
                'https://soundcloud.com/mosscaofficial/wax-motif-taiki-nulight-w-scrufizzer-skank-n-flex-mossca-flipexclusive')
        else:
            self.fail("Expected Track object")

    @patch('soundcloud_utils.requests.get')
    @patch('soundcloud_utils.SoundcloudAPI')
    def test_fetchTrack_http_mock(self, mock_soundcloud_api,
                                  mock_requests_get):
        # Simulate the HTTP response from the initial SoundCloud URL
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response
        # Mock the SoundcloudAPI resolve method to return a track
        mock_track = setupBasicTrack()
        mock_soundcloud_api.return_value.resolve.return_value = mock_track
        # URL to test
        mock_track_url = 'https://soundcloud.com/someTrack'
        # Call the fetchTrack function
        result = fetchTrack(mock_track_url)
        # Assertions
        if isinstance(result, Track):
            self.assertEqual(result.title, 'Mock Track Title')
            self.assertEqual(result.artist, 'Mock Artist')
            mock_requests_get.assert_not_called()
            mock_soundcloud_api.return_value.resolve.assert_called_once_with(
                'https://soundcloud.com/someTrack')
        else:
            self.fail("This test is intentionally failing.")

    @patch('soundcloud_utils.requests.get')
    @patch('soundcloud_utils.SoundcloudAPI')
    def test_fetchTrack_http_error(self, mock_soundcloud_api,
                                   mock_requests_get):
        # Simulate the HTTP response from the initial SoundCloud URL
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests_get.return_value = mock_response
        # URL to test
        mock_track_url = 'https://on.soundcloud.com/auqhgASa'

        # Assertions
        with self.assertRaises(Exception) as e:
            # Call the fetchTrack function
            fetchTrack(mock_track_url)
        self.assertEqual(str(e.exception),
                         "Unable to fetch Soundcloud Mobile URL")
        mock_requests_get.assert_called_once_with(mock_track_url, allow_redirects=True)
        mock_soundcloud_api.return_value.resolve.assert_not_called()

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts(self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrack()
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        expected_parts = {
            'embedPlatformType': 'soundcloud',
            'embedColour': 0xff5500,
            'title': f'{mock_track.artist} - {mock_track.title}',
            'Duration': '`2:03`',
            'Uploaded on': '1 January 2022',
            'Channel': '[Mock Artist](https://soundcloud.com/mockartist)',
            'Likes': ':orange_heart: 123',
            'thumbnailUrl': 'https://example.com/track-artwork.jpg',
            'Plays': ':notes: 456'
        }
        self.assertEqual(result, expected_parts)

        mock_fetch_track.assert_called_once_with(
            'https://soundcloud.com/someTrack')

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_downloadLink(self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrackWithBuyLinkDownload()
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        expected_parts = {
            'Buy/Download Link': ':arrow_down: [Download](<test@test.com>)'
        }
        self.assertTrue(
            all(item in result.items() for item in expected_parts.items()))

        mock_fetch_track.assert_called_once_with(
            'https://soundcloud.com/someTrack')

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_BuyLink(self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrackWithBuyLinkBuy()
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        expected_parts = {
            'Buy/Download Link': ':link: [Buy/Stream](<test@test.com>)',
        }
        self.assertTrue(
            all(item in result.items() for item in expected_parts.items()))

        mock_fetch_track.assert_called_once_with(
            'https://soundcloud.com/someTrack')

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_DirectDownload(self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrackWithDirectDownloadEnabled()
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        expected_parts = {
            'description':
            ':arrow_down: **Download button is on**'
            ' :arrow_down:[here](<test@test.com>)',
        }
        self.assertTrue(
            all(item in result.items() for item in expected_parts.items()))

        mock_fetch_track.assert_called_once_with(
            'https://soundcloud.com/someTrack')

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_DefinedArtist(self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrack()
        customArtist = 'My Custom Artist'
        mock_track.publisher_metadata = {'artist': customArtist}
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert

        expected_title = f'{customArtist} - {mock_track.title}'

        self.assertEqual(result['title'], expected_title)

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_DefinedArtistRemixArtist(
            self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrack()
        customArtist = 'My Custom Artist'
        mock_track.publisher_metadata = {'artist': customArtist}
        mock_track.title = f'Mock Track Title ({customArtist} Remix)'
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        expected_title = f'Mock Artist - Mock Track Title ({customArtist} Remix)'

        self.assertEqual(result['title'], expected_title)

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_DefinedArtistRemixArtistSameChannel(
            self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrack()
        mock_track.title = f'Mock Track Title ({mock_track.artist} Remix)'
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        expected_title = 'Mock Track Title (Mock Artist Remix)'

        self.assertEqual(result['title'], expected_title)

    # @patch('soundcloud_utils.fetchTrack')
    # def test_getSoundcloudParts_DefinedComposerOnlyPromotionalChannel(
    #         self, mock_fetch_track):
    #     # Arrange
    #     mock_track = setupBasicTrack()
    #     mock_track.publisher_metadata = {
    #         'writer_composer': 'Composer Name',
    #         'artist': 'Promotional Channel'
    #     }
    #     mock_track.user = {
    #         'username': 'Promotional Channel',
    #         'permalink_url': 'https://soundcloud.com/promotional-channel'
    #     }
    #     mock_fetch_track.return_value = mock_track

    #     # Act
    #     result = getSoundcloudParts('https://soundcloud.com/someTrack')

    #     # Assert
    #     expected_title = 'Composer Name - Mock Track Title'

    #     self.assertEqual(result['title'], expected_title)

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_UndefinedArtistPromotionalChannel(
            self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrack()
        mock_track.publisher_metadata = {'artist': 'Promotional Channel'}
        mock_track.user = {
            'username': 'Promotional Channel',
            'permalink_url': 'https://soundcloud.com/promotional-channel'
        }
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        expected_title = 'Mock Artist - Mock Track Title'

        self.assertEqual(result['title'], expected_title)

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_DefinedArtistPromotionalChannel(
            self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrack()
        mock_track.publisher_metadata = {
            'writer_composer': 'Composer Name',
            'artist': 'Featured Artist'
        }
        mock_track.user = {
            'username': 'Promotional Channel',
            'permalink_url': 'https://soundcloud.com/promotional-channel'
        }

        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        expected_title = 'Featured Artist - Mock Track Title'

        self.assertEqual(result['title'], expected_title)

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_HyphenatedArtistName(self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrack()
        mock_track.artist = 'dis'
        mock_track.title = 'joint - Mock Track Title'
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        expected_title = 'dis-joint - Mock Track Title'

        self.assertEqual(result['title'], expected_title)

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_ThumbnailUrl_WithArtwork(
            self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrack()
        mock_track.artwork_url = 'https://example.com/artwork.jpg'
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        self.assertEqual(result['thumbnailUrl'],
                         'https://example.com/artwork.jpg')

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_ThumbnailUrl_NoArtworkFallbackToAvatar(
            self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrack()
        mock_track.artwork_url = None
        mock_track.user['avatar_url'] = 'https://example.com/avatar.jpg'
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        self.assertEqual(result['thumbnailUrl'],
                         'https://example.com/avatar.jpg')

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_ThumbnailUrl_EmptyArtworkFallbackToAvatar(
            self, mock_fetch_track):
        # Arrange
        mock_track = setupBasicTrack()
        mock_track.artwork_url = ''
        mock_track.user['avatar_url'] = 'https://example.com/avatar.jpg'
        mock_fetch_track.return_value = mock_track

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someTrack')

        # Assert
        self.assertEqual(result['thumbnailUrl'],
                         'https://example.com/avatar.jpg')

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_ThumbnailUrl_PlaylistWithArtwork(
            self, mock_fetch_track):
        # Arrange
        mock_playlist = setupBasicPlaylist()
        mock_fetch_track.return_value = mock_playlist

        # Act
        result = getSoundcloudParts('https://soundcloud.com/somePlaylist')

        # Assert
        self.assertEqual(result['thumbnailUrl'],
                         'https://example.com/playlist-artwork.jpg')

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_ThumbnailUrl_PlaylistNoArtworkFallbackToFirstTrack(
            self, mock_fetch_track):
        # Arrange
        mock_first_track = setupBasicTrack()
        mock_first_track.artwork_url = 'https://example.com/first-track-artwork.jpg'

        mock_playlist = setupBasicPlaylist()
        mock_playlist.artwork_url = None
        mock_playlist.track_count = 1
        mock_playlist.tracks = [mock_first_track]
        mock_fetch_track.return_value = mock_playlist

        # Act
        result = getSoundcloudParts('https://soundcloud.com/somePlaylist')

        # Assert
        self.assertEqual(result['thumbnailUrl'],
                         'https://example.com/first-track-artwork.jpg')

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_ThumbnailUrl_AlbumWithArtwork(
            self, mock_fetch_track):
        # Arrange
        mock_album = setupBasicAlbum()
        mock_fetch_track.return_value = mock_album

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someAlbum')

        # Assert
        self.assertEqual(result['thumbnailUrl'],
                         'https://example.com/album-artwork.jpg')

    @patch('soundcloud_utils.fetchTrack')
    def test_getSoundcloudParts_ThumbnailUrl_AlbumNoArtworkFallbackToFirstTrack(
            self, mock_fetch_track):
        # Arrange
        mock_first_track = setupBasicTrack()
        mock_first_track.artwork_url = 'https://example.com/track-artwork.jpg'

        mock_album = setupBasicAlbum()
        mock_album.artwork_url = ''
        mock_album.track_count = 1
        mock_album.genre = 'Jazz'
        mock_album.user = {
            'username': 'Jazz Artist',
            'permalink_url': 'https://soundcloud.com/jazzartist'
        }
        mock_album.tracks = [mock_first_track]
        mock_fetch_track.return_value = mock_album

        # Act
        result = getSoundcloudParts('https://soundcloud.com/someAlbum')

        # Assert
        self.assertEqual(result['thumbnailUrl'],
                         'https://example.com/track-artwork.jpg')
