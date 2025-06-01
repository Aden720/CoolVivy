import unittest
from unittest.mock import patch

from mockData.youtube_mock_scenarios import setupBasicVideo

from youtube_utils import getYouTubeParts, isYoutubeMusic


class TestYoutubeUtils(unittest.TestCase):

    def test_isYoutubeMusic(self):
        self.assertTrue(isYoutubeMusic('MUSIC_VIDEO_TYPE_ATV'))
        self.assertTrue(isYoutubeMusic('MUSIC_VIDEO_TYPE_OMV'))
        self.assertFalse(isYoutubeMusic('MUSIC_VIDEO_TYPE_UGC'))
        self.assertFalse(isYoutubeMusic(None))

    @patch('youtube_utils.fetchTrack')
    def test_getYouTubeParts_topic_channel(self, mock_fetch_track):
        # Arrange
        mock_video = setupBasicVideo()
        mock_fetch_track.return_value = (mock_video, 1)  # 1 is types.track

        # Act
        result = getYouTubeParts('https://www.youtube.com/watch?v=123456789')

        # Assert
        self.assertEqual(result['title'], 'Mock Video Title')
        self.assertEqual(
            result['Artist'],
            '[Mock Artist](https://music.youtube.com/channel/UC123456789)')
        self.assertEqual(result['Duration'], '`3:00`')
        self.assertEqual(result['embedPlatformType'], 'youtubemusic')

    @patch('youtube_utils.fetchTrack')
    def test_getYouTubeParts_release_topic(self, mock_fetch_track):
        # Arrange
        mock_video = setupBasicVideo()
        mock_video['microformat']['microformatDataRenderer'][
            'pageOwnerDetails']['name'] = 'Release - Topic'
        mock_fetch_track.return_value = (mock_video, 1)

        # Act
        result = getYouTubeParts('https://www.youtube.com/watch?v=123456789')

        # Assert
        self.assertEqual(result['title'], 'Mock Video Title')
        self.assertEqual(
            result['Artist'],
            '[Mock Artist](https://music.youtube.com/channel/UC123456789)')

    @patch('youtube_utils.fetchTrack')
    def test_getYouTubeParts_non_music_video(self, mock_fetch_track):
        # Arrange
        mock_video = setupBasicVideo()
        mock_video['videoDetails']['musicVideoType'] = 'MUSIC_VIDEO_TYPE_UGC'
        mock_fetch_track.return_value = (mock_video, 1)

        # Act
        result = getYouTubeParts('https://www.youtube.com/watch?v=123456789')

        # Assert
        self.assertEqual(result['embedPlatformType'], 'youtube')
        self.assertEqual(
            result['Channel'],
            '[Mock Artist](https://www.youtube.com/channel/UC123456789)')

    @patch('youtube_utils.fetchTrack')
    def test_getYouTubeParts_no_track_found(self, mock_fetch_track):
        # Arrange
        mock_fetch_track.return_value = (None, None)

        # Act
        # Act & Assert
        with self.assertRaises(Exception) as context:
            getYouTubeParts('https://www.youtube.com/watch?v=123456789')

        # Assert
        self.assertIn("An error occurred while fetching Youtube details: no track",
                      str(context.exception))
