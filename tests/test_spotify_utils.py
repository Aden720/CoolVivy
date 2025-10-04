# test_spotify_utils.py
import logging
import unittest
from unittest.mock import MagicMock, patch

from spotify_utils import getSpotifyParts


class TestSpotifyUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Suppress logging output during tests
        logging.getLogger('spotify_utils').setLevel(logging.CRITICAL)

    def setUp(self):
        self.mock_sp = MagicMock()

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_track_basic(self, mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp

        mock_track = {
            'name':
            'Test Song',
            'artists': [{
                'name': 'Test Artist',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/artist/123'
                }
            }],
            'album': {
                'name': 'Test Album',
                'images': [{
                    'url': 'https://example.com/album-art.jpg'
                }],
                'release_date': '2023-01-15',
                'release_date_precision': 'day',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/album/456'
                },
                'total_tracks': 10
            },
            'duration_ms':
            210000,
            'external_urls': {
                'spotify': 'https://open.spotify.com/track/789'
            }
        }

        self.mock_sp.track.return_value = mock_track

        # Act
        result = getSpotifyParts('https://open.spotify.com/track/789')

        # Assert
        expected_parts = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954,
            'Duration': '`3:30`',
            'Released': '15 January 2023',
            'thumbnailUrl': 'https://example.com/album-art.jpg',
            'Artist': '[Test Artist](https://open.spotify.com/artist/123)',
            'Album': '[Test Album](https://open.spotify.com/album/456)',
            'title': 'Test Artist - Test Song'
        }

        for key, value in expected_parts.items():
            self.assertEqual(result[key], value)

        self.mock_sp.track.assert_called_once_with(
            'https://open.spotify.com/track/789')

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_track_multiple_artists(self, mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp

        mock_track = {
            'name':
            'Collaboration Song',
            'artists': [{
                'name': 'Artist One',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/artist/1'
                }
            }, {
                'name': 'Artist Two',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/artist/2'
                }
            }],
            'album': {
                'name': 'Collab Album',
                'images': [{
                    'url': 'https://example.com/collab-art.jpg'
                }],
                'release_date': '2023-06',
                'release_date_precision': 'month',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/album/collab'
                },
                'total_tracks': 5
            },
            'duration_ms':
            180000
        }

        self.mock_sp.track.return_value = mock_track

        # Act
        result = getSpotifyParts('https://open.spotify.com/track/collab-track')

        # Assert
        self.assertEqual(
            result['Artists'],
            '[Artist One](https://open.spotify.com/artist/1), [Artist Two](https://open.spotify.com/artist/2)'
        )
        self.assertEqual(result['Released'], 'June 2023')
        self.assertEqual(result['title'],
                         'Artist One, Artist Two - Collaboration Song')

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_track_single_track_album(self,
                                                      mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp

        mock_track = {
            'name':
            'Single Track',
            'artists': [{
                'name': 'Solo Artist',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/artist/solo'
                }
            }],
            'album': {
                'name': 'Single Release',
                'images': [{
                    'url': 'https://example.com/single-art.jpg'
                }],
                'release_date': '2023',
                'release_date_precision': 'year',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/album/single'
                },
                'total_tracks': 1
            },
            'duration_ms':
            240000
        }

        self.mock_sp.track.return_value = mock_track

        # Act
        result = getSpotifyParts('https://open.spotify.com/track/single-track')

        # Assert
        # Single track albums shouldn't show Album field
        self.assertNotIn('Album', result)
        self.assertEqual(result['Released'], '2023')
        self.assertEqual(result['Duration'], '`4:00`')

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_album_basic(self, mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp

        mock_album = {
            'name':
            'Test Album',
            'artists': [{
                'name': 'Test Artist',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/artist/test'
                }
            }],
            'images': [{
                'url': 'https://example.com/album-cover.jpg'
            }],
            'release_date':
            '2023-03-15',
            'release_date_precision':
            'day',
            'total_tracks':
            3,
            'label':
            'Test Records',
            'tracks': {
                'items': [{
                    'name': 'Track One',
                    'artists': [{
                        'name': 'Test Artist'
                    }],
                    'duration_ms': 180000,
                    'track_number': 1,
                    'external_urls': {
                        'spotify': 'https://open.spotify.com/track/1'
                    }
                }, {
                    'name': 'Track Two',
                    'artists': [{
                        'name': 'Test Artist'
                    }],
                    'duration_ms': 200000,
                    'track_number': 2,
                    'external_urls': {
                        'spotify': 'https://open.spotify.com/track/2'
                    }
                }]
            }
        }

        self.mock_sp.album.return_value = mock_album

        # Act
        result = getSpotifyParts('https://open.spotify.com/album/test-album')

        # Assert
        expected_parts = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954,
            'Duration': '`6:20`',
            'Artist': '[Test Artist](https://open.spotify.com/artist/test)',
            'Label': 'Test Records',
            'thumbnailUrl': 'https://example.com/album-cover.jpg',
            'description': '3 track album',
            'Released': '15 March 2023',
            'title': 'Test Artist - Test Album'
        }

        for key, value in expected_parts.items():
            self.assertEqual(result[key], value)

        self.assertIn('Tracks', result)
        self.assertIn(
            '1. [Track One](https://open.spotify.com/track/1) `3:00`',
            result['Tracks'])

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_album_various_artists(self, mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp

        mock_album = {
            'name':
            'Compilation Album',
            'artists': [{
                'name': 'Various Artists',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/artist/various'
                }
            }],
            'images': [{
                'url': 'https://example.com/compilation.jpg'
            }],
            'release_date':
            '2023-12-01',
            'release_date_precision':
            'day',
            'total_tracks':
            2,
            'tracks': {
                'items': [{
                    'name': 'Song A',
                    'artists': [{
                        'name': 'Artist A'
                    }],
                    'duration_ms': 150000,
                    'track_number': 1,
                    'external_urls': {
                        'spotify': 'https://open.spotify.com/track/a'
                    }
                }, {
                    'name': 'Song B',
                    'artists': [{
                        'name': 'Artist B'
                    }],
                    'duration_ms': 170000,
                    'track_number': 2,
                    'external_urls': {
                        'spotify': 'https://open.spotify.com/track/b'
                    }
                }]
            }
        }

        self.mock_sp.album.return_value = mock_album

        # Act
        result = getSpotifyParts('https://open.spotify.com/album/compilation')

        # Assert
        self.assertEqual(result['Artists'], 'Various Artists')
        self.assertEqual(result['title'], 'Compilation Album')
        self.assertIn('[Artist A - Song A]', result['Tracks'])
        self.assertIn('[Artist B - Song B]', result['Tracks'])

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_playlist_basic(self, mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp

        mock_playlist = {
            'name': 'My Playlist',
            'owner': {
                'display_name': 'Test User',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/user/testuser'
                }
            },
            'followers': {
                'total': 150
            },
            'images': [{
                'url': 'https://example.com/playlist.jpg'
            }],
            'description': 'A test playlist',
            'tracks': {
                'total':
                2,
                'items': [{
                    'track': {
                        'name': 'Playlist Song 1',
                        'artists': [{
                            'name': 'Playlist Artist 1'
                        }],
                        'duration_ms': 200000,
                        'external_urls': {
                            'spotify': 'https://open.spotify.com/track/p1'
                        }
                    }
                }, {
                    'track': {
                        'name': 'Playlist Song 2',
                        'artists': [{
                            'name': 'Playlist Artist 2'
                        }],
                        'duration_ms': 180000,
                        'external_urls': {
                            'spotify': 'https://open.spotify.com/track/p2'
                        }
                    }
                }],
                'next':
                None
            }
        }

        self.mock_sp.playlist.return_value = mock_playlist
        self.mock_sp.next.return_value = None

        # Act
        result = getSpotifyParts(
            'https://open.spotify.com/playlist/test-playlist')

        # Assert
        expected_parts = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954,
            'title': 'My Playlist',
            'Duration': '`6:20`',
            'Created by':
            '[Test User](https://open.spotify.com/user/testuser)',
            'Saves': '`150`',
            'thumbnailUrl': 'https://example.com/playlist.jpg',
            'Description': 'A test playlist',
            'description': 'Playlist (2 songs)'
        }

        for key, value in expected_parts.items():
            self.assertEqual(result[key], value)

        self.assertIn('Tracks', result)
        self.assertIn('1. [Playlist Artist 1 - Playlist Song 1]',
                      result['Tracks'])

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_track_with_remix_title(self, mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp

        mock_track = {
            'name':
            'Original Song - Remixer Remix',
            'artists': [{
                'name': 'Original Artist',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/artist/original'
                }
            }],
            'album': {
                'name': 'Remix Album',
                'images': [{
                    'url': 'https://example.com/remix.jpg'
                }],
                'release_date': '2023-05-20',
                'release_date_precision': 'day',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/album/remix'
                },
                'total_tracks': 1
            },
            'duration_ms':
            220000
        }

        self.mock_sp.track.return_value = mock_track

        # Act
        result = getSpotifyParts('https://open.spotify.com/track/remix-track')

        # Assert
        self.assertEqual(result['title'],
                         'Original Artist - Original Song (Remixer Remix)')

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_error_handling(self, mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp
        self.mock_sp.track.side_effect = Exception('API Error')

        # Act
        result = getSpotifyParts('https://open.spotify.com/track/error-track')

        # Assert
        expected_parts = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954
        }

        for key, value in expected_parts.items():
            self.assertEqual(result[key], value)

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_track_no_data(self, mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp
        self.mock_sp.track.return_value = None

        # Act
        result = getSpotifyParts('https://open.spotify.com/track/no-data')

        # Assert
        expected_parts = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954
        }

        for key, value in expected_parts.items():
            self.assertEqual(result[key], value)

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_intl_track_basic(self, mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp

        mock_track = {
            'name':
            'German Track',
            'artists': [{
                'name': 'German Artist',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/artist/german123'
                }
            }],
            'album': {
                'name': 'German Album',
                'images': [{
                    'url': 'https://example.com/german-art.jpg'
                }],
                'release_date': '2023-10-15',
                'release_date_precision': 'day',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/album/german456'
                },
                'total_tracks': 12
            },
            'duration_ms':
            195000,
            'external_urls': {
                'spotify':
                'https://open.spotify.com/track/1QeliItLbS0fvWbJA2dxMX'
            }
        }

        self.mock_sp.track.return_value = mock_track

        # Act
        result = getSpotifyParts(
            'https://open.spotify.com/intl-de/track/1QeliItLbS0fvWbJA2dxMX')

        # Assert
        expected_parts = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954,
            'Duration': '`3:15`',
            'Released': '15 October 2023',
            'thumbnailUrl': 'https://example.com/german-art.jpg',
            'Artist':
            '[German Artist](https://open.spotify.com/artist/german123)',
            'Album':
            '[German Album](https://open.spotify.com/album/german456)',
            'title': 'German Artist - German Track'
        }

        for key, value in expected_parts.items():
            self.assertEqual(result[key], value)

        self.mock_sp.track.assert_called_once_with(
            'https://open.spotify.com/intl-de/track/1QeliItLbS0fvWbJA2dxMX')

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_intl_album_basic(self, mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp

        mock_album = {
            'name':
            'International Album',
            'artists': [{
                'name': 'International Artist',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/artist/intl'
                }
            }],
            'images': [{
                'url': 'https://example.com/intl-album.jpg'
            }],
            'release_date':
            '2023-08-20',
            'release_date_precision':
            'day',
            'total_tracks':
            4,
            'label':
            'International Records',
            'tracks': {
                'items': [{
                    'name': 'Intl Track One',
                    'artists': [{
                        'name': 'International Artist'
                    }],
                    'duration_ms': 210000,
                    'track_number': 1,
                    'external_urls': {
                        'spotify': 'https://open.spotify.com/track/intl1'
                    }
                }, {
                    'name': 'Intl Track Two',
                    'artists': [{
                        'name': 'International Artist'
                    }],
                    'duration_ms': 185000,
                    'track_number': 2,
                    'external_urls': {
                        'spotify': 'https://open.spotify.com/track/intl2'
                    }
                }]
            }
        }

        self.mock_sp.album.return_value = mock_album

        # Act
        result = getSpotifyParts(
            'https://open.spotify.com/intl-fr/album/test-intl-album')

        # Assert
        expected_parts = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954,
            'Duration': '`6:35`',
            'Artist':
            '[International Artist](https://open.spotify.com/artist/intl)',
            'Label': 'International Records',
            'thumbnailUrl': 'https://example.com/intl-album.jpg',
            'description': '4 track album',
            'Released': '20 August 2023',
            'title': 'International Artist - International Album'
        }

        for key, value in expected_parts.items():
            self.assertEqual(result[key], value)

        self.assertIn('Tracks', result)
        self.assertIn(
            '1. [Intl Track One](https://open.spotify.com/track/intl1) `3:30`',
            result['Tracks'])

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_intl_playlist_basic(self, mock_spotify_class):
        # Arrange
        mock_spotify_class.return_value = self.mock_sp

        mock_playlist = {
            'name': 'International Playlist',
            'owner': {
                'display_name': 'International User',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/user/intluser'
                }
            },
            'followers': {
                'total': 500
            },
            'images': [{
                'url': 'https://example.com/intl-playlist.jpg'
            }],
            'description': 'A playlist with international music',
            'tracks': {
                'total':
                3,
                'items': [{
                    'track': {
                        'name': 'International Song 1',
                        'artists': [{
                            'name': 'Artist One'
                        }],
                        'duration_ms': 220000,
                        'external_urls': {
                            'spotify':
                            'https://open.spotify.com/track/intl-song1'
                        }
                    }
                }, {
                    'track': {
                        'name': 'International Song 2',
                        'artists': [{
                            'name': 'Artist Two'
                        }],
                        'duration_ms': 195000,
                        'external_urls': {
                            'spotify':
                            'https://open.spotify.com/track/intl-song2'
                        }
                    }
                }, {
                    'track': {
                        'name': 'International Song 3',
                        'artists': [{
                            'name': 'Artist Three'
                        }],
                        'duration_ms': 175000,
                        'external_urls': {
                            'spotify':
                            'https://open.spotify.com/track/intl-song3'
                        }
                    }
                }],
                'next':
                None
            }
        }

        self.mock_sp.playlist.return_value = mock_playlist
        self.mock_sp.next.return_value = None

        # Act
        result = getSpotifyParts(
            'https://open.spotify.com/intl-es/playlist/test-intl-playlist')

        # Assert
        expected_parts = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954,
            'title': 'International Playlist',
            'Duration': '`9:50`',
            'Created by':
            '[International User](https://open.spotify.com/user/intluser)',
            'Saves': '`500`',
            'thumbnailUrl': 'https://example.com/intl-playlist.jpg',
            'Description': 'A playlist with international music',
            'description': 'Playlist (3 songs)'
        }

        for key, value in expected_parts.items():
            self.assertEqual(result[key], value)

        self.assertIn('Tracks', result)
        self.assertIn('1. [Artist One - International Song 1]',
                      result['Tracks'])
        self.assertIn('1. [Artist Two - International Song 2]',
                      result['Tracks'])

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_various_intl_codes(self, mock_spotify_class):
        # Test various international codes work properly
        mock_spotify_class.return_value = self.mock_sp

        mock_track = {
            'name':
            'Test Track',
            'artists': [{
                'name': 'Test Artist',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/artist/test'
                }
            }],
            'album': {
                'name': 'Test Album',
                'images': [{
                    'url': 'https://example.com/test.jpg'
                }],
                'release_date': '2023-01-01',
                'release_date_precision': 'day',
                'external_urls': {
                    'spotify': 'https://open.spotify.com/album/test'
                },
                'total_tracks': 1
            },
            'duration_ms':
            180000
        }

        self.mock_sp.track.return_value = mock_track

        # Test different international codes
        intl_urls = [
            'https://open.spotify.com/intl-de/track/test',
            'https://open.spotify.com/intl-fr/track/test',
            'https://open.spotify.com/intl-es/track/test',
            'https://open.spotify.com/intl-it/track/test',
            'https://open.spotify.com/intl-pt/track/test',
            'https://open.spotify.com/intl-ja/track/test',
            'https://open.spotify.com/intl-ko/track/test'
        ]

        for url in intl_urls:
            with self.subTest(url=url):
                result = getSpotifyParts(url)

                # Should successfully process all international URLs
                self.assertEqual(result['embedPlatformType'], 'spotify')
                self.assertEqual(result['embedColour'], 0x1db954)
                self.assertEqual(result['title'], 'Test Artist - Test Track')
                self.assertEqual(result['Duration'], '`3:00`')

    @patch('spotify_utils.spotipy.Spotify')
    def test_getSpotifyParts_intl_url_edge_cases(self, mock_spotify_class):
        # Test edge cases with international URLs
        mock_spotify_class.return_value = self.mock_sp
        self.mock_sp.track.side_effect = Exception('API Error')

        # Test that international URLs still handle errors gracefully
        result = getSpotifyParts(
            'https://open.spotify.com/intl-unknown/track/error-track')

        # Should still return basic structure on error
        expected_parts = {
            'embedPlatformType': 'spotify',
            'embedColour': 0x1db954
        }

        for key, value in expected_parts.items():
            self.assertEqual(result[key], value)


if __name__ == '__main__':
    unittest.main()
