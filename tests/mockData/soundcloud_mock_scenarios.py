from unittest.mock import MagicMock

from sclib import Track


def setupBasicEmbed():
    embed = MagicMock()
    embed.url = 'https://soundcloud.com/someTrack'
    return embed


def setupBasicTrack():
    mock_track = MagicMock(spec=Track)
    mock_track.artist = 'Mock Artist'
    mock_track.title = 'Mock Track Title'
    mock_track.genre = ''
    mock_track.duration = 123456
    mock_track.created_at = '2022-01-01T00:00:00Z'
    mock_track.likes_count = 123
    mock_track.playback_count = 456
    mock_track.publisher_metadata = {}
    mock_track.tag_list = ''
    mock_track.purchase_title = ''
    mock_track.purchase_url = ''
    mock_track.user = {}
    mock_track.publisher_metadata = {}
    return mock_track


def setupBasicTrackWithLikes():
    mock_track = setupBasicTrack()
    mock_track.likes_count = 100
    return mock_track


def setupBasicTrackWithTags():
    mock_track = setupBasicTrack()
    mock_track.tag_list = '"Mock Tag1", "Mock Tag2"'
    return mock_track
