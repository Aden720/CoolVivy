# test_soundcloud_utils.py
import unittest
from unittest.mock import MagicMock, patch

from mockData.soundcloud_mock_scenarios import setupBasicTrack
from sclib import Track

from soundcloud_utils import fetchTrack, split_tags


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
            mock_requests_get.assert_called_once_with(mock_track_url)
            mock_soundcloud_api.return_value.resolve.assert_called_once_with(
                'https://soundcloud.com/resolved-url')
        else:  
            self.fail("This test is intentionally failing.")

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
        self.assertEqual(result.title, 'Mock Track Title')
        self.assertEqual(result.artist, 'Mock Artist')
        self.assertEqual(result.title, 'Mock Track Title')
        mock_requests_get.assert_not_called()
        mock_soundcloud_api.return_value.resolve.assert_called_once_with(
            'https://soundcloud.com/someTrack')