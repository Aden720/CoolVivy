import logging
import unittest
from unittest.mock import MagicMock, patch

from spotify_utils import getSpotifyParts


def _make_track_response(
    name='Test Song',
    track_id='789',
    track_uri='spotify:track:789',
    duration_ms=210000,
    first_artist_name='Test Artist',
    first_artist_id='123',
    first_artist_uri='spotify:artist:123',
    other_artists=None,
    album_name='Test Album',
    album_id='456',
    album_uri='spotify:album:456',
    date_iso='2023-01-15T00:00:00Z',
    date_precision='DAY',
    date_year=2023,
    cover_url='https://example.com/album-art.jpg',
    album_total_tracks=10,
):
    return {
        'data': {
            'trackUnion': {
                'name': name,
                'id': track_id,
                'uri': track_uri,
                'duration': {'totalMilliseconds': duration_ms},
                'firstArtist': {
                    'items': [{
                        'id': first_artist_id,
                        'profile': {'name': first_artist_name},
                        'uri': first_artist_uri,
                    }]
                },
                'otherArtists': {
                    'items': other_artists or []
                },
                'albumOfTrack': {
                    'name': album_name,
                    'id': album_id,
                    'uri': album_uri,
                    'date': {
                        'isoString': date_iso,
                        'precision': date_precision,
                        'year': date_year,
                    },
                    'coverArt': {
                        'sources': [{'url': cover_url, 'height': 640, 'width': 640}]
                    },
                    'tracks': {'totalCount': album_total_tracks},
                },
            }
        }
    }


def _make_album_response(
    name='Test Album',
    album_uri='spotify:album:test-album',
    artists=None,
    date_iso='2023-03-15T00:00:00Z',
    date_precision='DAY',
    date_year=2023,
    cover_url='https://example.com/album-cover.jpg',
    label='Test Records',
    total_tracks=3,
    track_items=None,
):
    if artists is None:
        artists = [{
            'id': 'test',
            'profile': {'name': 'Test Artist'},
            'uri': 'spotify:artist:test',
        }]
    if track_items is None:
        track_items = [
            {
                'track': {
                    'name': 'Track One',
                    'trackNumber': 1,
                    'uri': 'spotify:track:1',
                    'duration': {'totalMilliseconds': 180000},
                    'artists': {'items': [{'profile': {'name': 'Test Artist'}, 'uri': 'spotify:artist:test'}]},
                }
            },
            {
                'track': {
                    'name': 'Track Two',
                    'trackNumber': 2,
                    'uri': 'spotify:track:2',
                    'duration': {'totalMilliseconds': 200000},
                    'artists': {'items': [{'profile': {'name': 'Test Artist'}, 'uri': 'spotify:artist:test'}]},
                }
            },
        ]
    return {
        'data': {
            'albumUnion': {
                'name': name,
                'uri': album_uri,
                'artists': {'items': artists},
                'date': {
                    'isoString': date_iso,
                    'precision': date_precision,
                    'year': date_year,
                },
                'coverArt': {
                    'sources': [{'url': cover_url, 'height': 640, 'width': 640}]
                },
                'label': label,
                'type': 'ALBUM',
                'tracksV2': {
                    'totalCount': total_tracks,
                    'items': track_items,
                },
            }
        }
    }


class TestSpotifyUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.getLogger('spotify_utils').setLevel(logging.CRITICAL)

    @patch('spotify_utils.Public.song_info')
    def test_getSpotifyParts_track_basic(self, mock_song_info):
        mock_song_info.return_value = _make_track_response()

        result = getSpotifyParts('https://open.spotify.com/track/789')

        expected = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954,
            'Duration': '`3:30`',
            'Released': '15 January 2023',
            'thumbnailUrl': 'https://example.com/album-art.jpg',
            'Artist': '[Test Artist](https://open.spotify.com/artist/123)',
            'Album': '[Test Album](https://open.spotify.com/album/456)',
            'title': 'Test Artist - Test Song',
        }
        for key, value in expected.items():
            self.assertEqual(result[key], value)

        mock_song_info.assert_called_once_with('789')

    @patch('spotify_utils.Public.song_info')
    def test_getSpotifyParts_track_multiple_artists(self, mock_song_info):
        mock_song_info.return_value = _make_track_response(
            name='Collaboration Song',
            first_artist_name='Artist One',
            first_artist_id='1',
            first_artist_uri='spotify:artist:1',
            other_artists=[{
                'id': '2',
                'profile': {'name': 'Artist Two'},
                'uri': 'spotify:artist:2',
            }],
            album_name='Collab Album',
            album_uri='spotify:album:collab',
            date_iso='2023-06-01T00:00:00Z',
            date_precision='MONTH',
            date_year=2023,
            duration_ms=180000,
        )

        result = getSpotifyParts('https://open.spotify.com/track/collab-track')

        self.assertEqual(
            result['Artists'],
            '[Artist One](https://open.spotify.com/artist/1), [Artist Two](https://open.spotify.com/artist/2)',
        )
        self.assertEqual(result['Released'], 'June 2023')
        self.assertEqual(result['title'], 'Artist One, Artist Two - Collaboration Song')

    @patch('spotify_utils.Public.song_info')
    def test_getSpotifyParts_track_single_track_album(self, mock_song_info):
        mock_song_info.return_value = _make_track_response(
            name='Single Track',
            first_artist_name='Solo Artist',
            first_artist_uri='spotify:artist:solo',
            album_name='Single Release',
            album_uri='spotify:album:single',
            date_iso='2023-01-01T00:00:00Z',
            date_precision='YEAR',
            date_year=2023,
            duration_ms=240000,
            album_total_tracks=1,
        )

        result = getSpotifyParts('https://open.spotify.com/track/single-track')

        self.assertNotIn('Album', result)
        self.assertEqual(result['Released'], '2023')
        self.assertEqual(result['Duration'], '`4:00`')

    @patch('spotify_utils.PublicAlbum')
    def test_getSpotifyParts_album_basic(self, mock_album_class):
        mock_instance = MagicMock()
        mock_album_class.return_value = mock_instance
        mock_instance.get_album_info.return_value = _make_album_response()

        result = getSpotifyParts('https://open.spotify.com/album/test-album')

        expected = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954,
            'Duration': '`6:20`',
            'Artist': '[Test Artist](https://open.spotify.com/artist/test)',
            'Label': 'Test Records',
            'thumbnailUrl': 'https://example.com/album-cover.jpg',
            'description': '3 track album',
            'Released': '15 March 2023',
            'title': 'Test Artist - Test Album',
        }
        for key, value in expected.items():
            self.assertEqual(result[key], value)

        self.assertIn('Tracks', result)
        self.assertIn('1. [Track One](https://open.spotify.com/track/1)', result['Tracks'])

    @patch('spotify_utils.PublicAlbum')
    def test_getSpotifyParts_album_various_artists(self, mock_album_class):
        mock_instance = MagicMock()
        mock_album_class.return_value = mock_instance
        mock_instance.get_album_info.return_value = _make_album_response(
            name='Compilation Album',
            album_uri='spotify:album:compilation',
            artists=[{
                'id': 'various',
                'profile': {'name': 'Various Artists'},
                'uri': 'spotify:artist:various',
            }],
            date_iso='2023-12-01T00:00:00Z',
            date_precision='DAY',
            date_year=2023,
            total_tracks=2,
            track_items=[
                {
                    'track': {
                        'name': 'Song A',
                        'trackNumber': 1,
                        'uri': 'spotify:track:a',
                        'duration': {'totalMilliseconds': 150000},
                        'artists': {'items': [{'profile': {'name': 'Artist A'}, 'uri': 'spotify:artist:a'}]},
                    }
                },
                {
                    'track': {
                        'name': 'Song B',
                        'trackNumber': 2,
                        'uri': 'spotify:track:b',
                        'duration': {'totalMilliseconds': 170000},
                        'artists': {'items': [{'profile': {'name': 'Artist B'}, 'uri': 'spotify:artist:b'}]},
                    }
                },
            ],
        )

        result = getSpotifyParts('https://open.spotify.com/album/compilation')

        self.assertEqual(result['Artists'], 'Various Artists')
        self.assertEqual(result['title'], 'Compilation Album')
        self.assertIn('[Artist A - Song A]', result['Tracks'])
        self.assertIn('[Artist B - Song B]', result['Tracks'])

    @patch('spotify_utils.Public.song_info')
    def test_getSpotifyParts_track_with_remix_title(self, mock_song_info):
        mock_song_info.return_value = _make_track_response(
            name='Original Song - Remixer Remix',
            first_artist_name='Original Artist',
            first_artist_uri='spotify:artist:original',
            album_uri='spotify:album:remix',
            duration_ms=220000,
            album_total_tracks=1,
        )

        result = getSpotifyParts('https://open.spotify.com/track/remix-track')

        self.assertEqual(result['title'], 'Original Artist - Original Song (Remixer Remix)')

    @patch('spotify_utils.Public.song_info')
    def test_getSpotifyParts_error_handling(self, mock_song_info):
        mock_song_info.side_effect = Exception('API Error')

        result = getSpotifyParts('https://open.spotify.com/track/error-track')

        self.assertEqual(result['embedPlatformType'], 'spotify')
        self.assertEqual(result['embedColour'], 0x1db954)
        self.assertNotIn('title', result)

    @patch('spotify_utils.Public.song_info')
    def test_getSpotifyParts_track_no_data(self, mock_song_info):
        mock_song_info.return_value = None

        result = getSpotifyParts('https://open.spotify.com/track/no-data')

        self.assertEqual(result['embedPlatformType'], 'spotify')
        self.assertEqual(result['embedColour'], 0x1db954)
        self.assertNotIn('title', result)

    @patch('spotify_utils.Public.song_info')
    def test_getSpotifyParts_intl_track_basic(self, mock_song_info):
        mock_song_info.return_value = _make_track_response(
            name='German Track',
            first_artist_name='German Artist',
            first_artist_id='german123',
            first_artist_uri='spotify:artist:german123',
            album_name='German Album',
            album_id='german456',
            album_uri='spotify:album:german456',
            date_iso='2023-10-15T00:00:00Z',
            date_precision='DAY',
            date_year=2023,
            cover_url='https://example.com/german-art.jpg',
            duration_ms=195000,
            album_total_tracks=12,
        )

        result = getSpotifyParts(
            'https://open.spotify.com/intl-de/track/1QeliItLbS0fvWbJA2dxMX')

        expected = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954,
            'Duration': '`3:15`',
            'Released': '15 October 2023',
            'thumbnailUrl': 'https://example.com/german-art.jpg',
            'Artist': '[German Artist](https://open.spotify.com/artist/german123)',
            'Album': '[German Album](https://open.spotify.com/album/german456)',
            'title': 'German Artist - German Track',
        }
        for key, value in expected.items():
            self.assertEqual(result[key], value)

        mock_song_info.assert_called_once_with('1QeliItLbS0fvWbJA2dxMX')

    @patch('spotify_utils.PublicAlbum')
    def test_getSpotifyParts_intl_album_basic(self, mock_album_class):
        mock_instance = MagicMock()
        mock_album_class.return_value = mock_instance
        mock_instance.get_album_info.return_value = _make_album_response(
            name='International Album',
            album_uri='spotify:album:intl',
            artists=[{
                'id': 'intl',
                'profile': {'name': 'International Artist'},
                'uri': 'spotify:artist:intl',
            }],
            date_iso='2023-08-20T00:00:00Z',
            date_precision='DAY',
            date_year=2023,
            cover_url='https://example.com/intl-album.jpg',
            label='International Records',
            total_tracks=4,
            track_items=[
                {
                    'track': {
                        'name': 'Intl Track One',
                        'trackNumber': 1,
                        'uri': 'spotify:track:intl1',
                        'duration': {'totalMilliseconds': 210000},
                        'artists': {'items': [{'profile': {'name': 'International Artist'}, 'uri': 'spotify:artist:intl'}]},
                    }
                },
                {
                    'track': {
                        'name': 'Intl Track Two',
                        'trackNumber': 2,
                        'uri': 'spotify:track:intl2',
                        'duration': {'totalMilliseconds': 185000},
                        'artists': {'items': [{'profile': {'name': 'International Artist'}, 'uri': 'spotify:artist:intl'}]},
                    }
                },
            ],
        )

        result = getSpotifyParts(
            'https://open.spotify.com/intl-fr/album/test-intl-album')

        expected = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954,
            'Duration': '`6:35`',
            'Artist': '[International Artist](https://open.spotify.com/artist/intl)',
            'Label': 'International Records',
            'thumbnailUrl': 'https://example.com/intl-album.jpg',
            'description': '4 track album',
            'Released': '20 August 2023',
            'title': 'International Artist - International Album',
        }
        for key, value in expected.items():
            self.assertEqual(result[key], value)

        self.assertIn('Tracks', result)
        self.assertIn('1. [Intl Track One](https://open.spotify.com/track/intl1)', result['Tracks'])

    @patch('spotify_utils.PublicAlbum')
    def test_getSpotifyParts_album_error_handling(self, mock_album_class):
        mock_instance = MagicMock()
        mock_album_class.return_value = mock_instance
        mock_instance.get_album_info.side_effect = Exception('Network error')

        result = getSpotifyParts('https://open.spotify.com/album/error-album')

        self.assertEqual(result['embedPlatformType'], 'spotify')
        self.assertEqual(result['embedColour'], 0x1db954)
        self.assertNotIn('title', result)
