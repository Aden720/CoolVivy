from unittest.mock import MagicMock

from sclib import Playlist, Track


def setupBasicTrack():
    mock_track = MagicMock(spec=Track)
    mock_track.artist = 'Mock Artist'
    mock_track.title = 'Mock Track Title'
    mock_track.artwork_url = 'https://example.com/track-artwork.jpg'
    mock_track.genre = ''
    mock_track.duration = 123456
    mock_track.created_at = '2022-01-01T00:00:00Z'
    mock_track.likes_count = 123
    mock_track.playback_count = 456
    mock_track.publisher_metadata = {}
    mock_track.tag_list = ''
    mock_track.purchase_title = ''
    mock_track.purchase_url = ''
    mock_track.user = {
        'username': 'Mock Artist',
        'permalink_url': 'https://soundcloud.com/mockartist',
        'avatar_url': 'https://example.com/avatar.jpg'
    }
    mock_track.publisher_metadata = {}
    mock_track.is_downloadable = False
    mock_track.has_downloads_left = False
    return mock_track


def setupBasicTrackWithLikes():
    mock_track = setupBasicTrack()
    mock_track.likes_count = 100
    return mock_track


def setupBasicTrackWithDirectDownloadEnabled():
    mock_track = setupBasicTrack()
    mock_track.is_downloadable = True
    mock_track.has_downloads_left = True
    mock_track.download_url = 'test@test.com'
    return mock_track


def setupBasicTrackWithBuyLinkDownload():
    mock_track = setupBasicTrack()
    mock_track.purchase_title = 'Download'
    mock_track.purchase_url = 'test@test.com'
    return mock_track


def setupBasicTrackWithBuyLinkBuy():
    mock_track = setupBasicTrack()
    mock_track.purchase_title = 'Buy/Stream'
    mock_track.purchase_url = 'test@test.com'
    return mock_track


def setupBasicTrackWithTags():
    mock_track = setupBasicTrack()
    mock_track.tag_list = '"Mock Tag1", "Mock Tag2"'
    return mock_track


def setupBasicPlaylist():
    mock_playlist = MagicMock(spec=Playlist)
    mock_playlist.artwork_url = 'https://example.com/playlist-artwork.jpg'
    mock_playlist.is_album = False
    mock_playlist.track_count = 5
    mock_playlist.title = 'Test Playlist'
    mock_playlist.genre = 'Electronic'
    mock_playlist.duration = 1200000
    mock_playlist.likes_count = 50
    mock_playlist.tag_list = 'electronic deep'
    mock_playlist.tracks = []
    return mock_playlist


def setupBasicAlbum():
    mock_album = MagicMock(spec=Playlist)
    mock_album.artwork_url = 'https://example.com/album-artwork.jpg'
    mock_album.is_album = True
    mock_album.track_count = 10
    mock_album.title = 'Test Album'
    mock_album.genre = 'Rock'
    mock_album.duration = 2400000
    mock_album.likes_count = 100
    mock_album.tag_list = 'rock alternative'
    mock_album.user = {
        'username': 'Test Artist',
        'permalink_url': 'https://soundcloud.com/testartist'
    }
    mock_album.tracks = []
    return mock_album
