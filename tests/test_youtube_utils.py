import unittest
from unittest.mock import patch

from mockData.youtube_mock_scenarios import setupBasicVideo

from youtube_utils import fetchVideoDescription, getYouTubeParts, isYoutubeMusic


class TestYoutubeUtils(unittest.TestCase):

    def test_isYoutubeMusic(self):
        self.assertTrue(isYoutubeMusic('MUSIC_VIDEO_TYPE_ATV'))
        self.assertTrue(isYoutubeMusic('MUSIC_VIDEO_TYPE_OMV'))
        self.assertFalse(isYoutubeMusic('MUSIC_VIDEO_TYPE_UGC'))
        self.assertFalse(isYoutubeMusic(None))

    @patch('youtube_utils.fetchVideoDescription')
    @patch('youtube_utils.fetchTrack')
    def test_getYouTubeParts_topic_channel(self, mock_fetch_track, mock_fetch_description):
        # Arrange
        mock_video = setupBasicVideo()
        mock_fetch_track.return_value = (mock_video, 1)  # 1 is types.track
        mock_fetch_description.return_value = None

        # Act
        result = getYouTubeParts('https://www.youtube.com/watch?v=123456789')

        # Assert
        self.assertEqual(result['title'], 'Mock Video Title')
        self.assertEqual(
            result['Artist'],
            '[Mock Artist](https://music.youtube.com/channel/UC123456789)')
        self.assertEqual(result['Duration'], '`3:00`')
        self.assertEqual(result['embedPlatformType'], 'youtubemusic')

    @patch('youtube_utils.fetchVideoDescription')
    @patch('youtube_utils.fetchTrack')
    def test_getYouTubeParts_release_topic(self, mock_fetch_track, mock_fetch_description):
        # Arrange
        mock_video = setupBasicVideo()
        mock_video['microformat']['microformatDataRenderer'][
            'pageOwnerDetails']['name'] = 'Release - Topic'
        mock_fetch_track.return_value = (mock_video, 1)
        mock_fetch_description.return_value = None

        # Act
        result = getYouTubeParts('https://www.youtube.com/watch?v=123456789')

        # Assert
        self.assertEqual(result['title'], 'Mock Video Title')
        self.assertEqual(
            result['Artist'],
            '[Mock Artist](https://music.youtube.com/channel/UC123456789)')

    @patch('youtube_utils.fetchVideoDescription')
    @patch('youtube_utils.fetchTrack')
    def test_getYouTubeParts_non_music_video(self, mock_fetch_track, mock_fetch_description):
        # Arrange
        mock_video = setupBasicVideo()
        mock_video['videoDetails']['musicVideoType'] = 'MUSIC_VIDEO_TYPE_UGC'
        mock_fetch_track.return_value = (mock_video, 1)
        mock_fetch_description.return_value = None

        # Act
        result = getYouTubeParts('https://www.youtube.com/watch?v=123456789')

        # Assert
        self.assertEqual(result['embedPlatformType'], 'youtube')
        self.assertEqual(
            result['Channel'],
            '[Mock Artist](https://www.youtube.com/channel/UC123456789)')

    @patch('youtube_utils.fetchVideoDescription')
    @patch('youtube_utils.fetchTrack')
    def test_getYouTubeParts_no_track_found(self, mock_fetch_track, mock_fetch_description):
        # Arrange
        mock_fetch_track.return_value = (None, None)
        mock_fetch_description.return_value = None

        # Act
        # Act & Assert
        with self.assertRaises(Exception) as context:
            getYouTubeParts('https://www.youtube.com/watch?v=123456789')

        # Assert
        self.assertIn("An error occurred while fetching Youtube details: no track",
                      str(context.exception))

    @patch('youtube_utils.youtube_api')
    def test_fetchVideoDescription_success(self, mock_youtube_api):
        # Arrange
        mock_request = mock_youtube_api.videos.return_value.list.return_value
        mock_request.execute.return_value = {
            'items': [{
                'snippet': {
                    'description': 'Test video description\n\nProvided to YouTube by Mock\nMock Artist · Mock Title\n\nMock Album\n\nReleased on: 2024-01-01\n'
                }
            }]
        }
        
        # Act
        result = fetchVideoDescription('test_video_id')
        
        # Assert
        self.assertEqual(result, 'Test video description\n\nProvided to YouTube by Mock\nMock Artist · Mock Title\n\nMock Album\n\nReleased on: 2024-01-01\n')
        mock_youtube_api.videos.return_value.list.assert_called_once_with(part="snippet", id="test_video_id")

    @patch('youtube_utils.youtube_api')
    def test_fetchVideoDescription_no_video_found(self, mock_youtube_api):
        # Arrange
        mock_request = mock_youtube_api.videos.return_value.list.return_value
        mock_request.execute.return_value = {'items': []}
        
        # Act
        result = fetchVideoDescription('nonexistent_video_id')
        
        # Assert
        self.assertIsNone(result)

    @patch('youtube_utils.youtube_api')
    def test_fetchVideoDescription_api_exception(self, mock_youtube_api):
        # Arrange
        mock_request = mock_youtube_api.videos.return_value.list.return_value
        mock_request.execute.side_effect = Exception("API Error")
        
        # Act
        result = fetchVideoDescription('test_video_id')
        
        # Assert
        self.assertIsNone(result)

    @patch('youtube_utils.youtube_api', None)
    def test_fetchVideoDescription_no_api_key_configured(self):
        # Act
        result = fetchVideoDescription('test_video_id')
        
        # Assert
        self.assertIsNone(result)
