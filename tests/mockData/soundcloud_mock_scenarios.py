from unittest.mock import MagicMock

from sclib import Track


def setupBasicTrack():
    mock_track = MagicMock(spec=Track)
    mock_track.artist = 'Mock Artist'
    mock_track.title = 'Mock Track Title'
    return mock_track
