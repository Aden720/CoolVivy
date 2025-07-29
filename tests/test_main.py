import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from main import fetchEmbed, getDescriptionParts, getUserIdFromFooter, setAuthorLink
from object_types import CategorizedLink, link_types


class TestMainBot(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Create mock message and channel
        self.mock_message = MagicMock()
        self.mock_message.id = 123456789
        self.mock_message.channel = MagicMock()
        self.mock_message.channel.fetch_message = AsyncMock()
        self.mock_message.channel.permissions_for = MagicMock()
        self.mock_message.channel.permissions_for.return_value.manage_webhooks = False
        self.mock_message.guild = MagicMock()
        self.mock_message.guild.me = MagicMock()
        self.mock_message.author = MagicMock()
        self.mock_message.author.id = 987654321
        self.mock_message.author.display_name = "TestUser"
        self.mock_message.author.avatar = MagicMock()
        self.mock_message.author.avatar.url = "https://example.com/avatar.png"
        self.mock_message.content = "Check out this track!"
        self.mock_message.reference = None
        self.mock_message.reply = AsyncMock()
        self.mock_message.add_reaction = AsyncMock()
        self.mock_message.edit = AsyncMock()

    def test_getDescriptionParts_soundcloud(self):
        # Arrange
        link: CategorizedLink = ("https://soundcloud.com/artist/track",
                                 link_types.soundcloud)

        with patch('main.getSoundcloudParts') as mock_get_soundcloud:
            mock_get_soundcloud.return_value = {'title': 'Test Track'}

            # Act
            result = getDescriptionParts(link)

            # Assert
            self.assertEqual(result, {'title': 'Test Track'})
            mock_get_soundcloud.assert_called_once_with(link[0])

    def test_getDescriptionParts_youtube(self):
        # Arrange
        link: CategorizedLink = ("https://youtube.com/watch?v=test",
                                 link_types.youtube)

        with patch('main.getYouTubeParts') as mock_get_youtube:
            mock_get_youtube.return_value = {'title': 'Test Video'}

            # Act
            result = getDescriptionParts(link)

            # Assert
            self.assertEqual(result, {'title': 'Test Video'})
            mock_get_youtube.assert_called_once_with(link[0])

    def test_getDescriptionParts_spotify(self):
        # Arrange
        link: CategorizedLink = ("https://spotify.com/track/test",
                                 link_types.spotify)

        with patch('main.getSpotifyParts') as mock_get_spotify:
            mock_get_spotify.return_value = {'title': 'Test Song'}

            # Act
            result = getDescriptionParts(link)

            # Assert
            self.assertEqual(result, {'title': 'Test Song'})
            mock_get_spotify.assert_called_once_with(link[0])

    def test_getDescriptionParts_bandcamp(self):
        # Arrange
        link: CategorizedLink = ("https://artist.bandcamp.com/track/test",
                                 link_types.bandcamp)

        with patch('main.getBandcampParts') as mock_get_bandcamp:
            mock_get_bandcamp.return_value = {'title': 'Test Album'}

            # Act
            result = getDescriptionParts(link)

            # Assert
            self.assertEqual(result, {'title': 'Test Album'})
            mock_get_bandcamp.assert_called_once_with(link[0])

    def test_getDescriptionParts_bandcamp_main_site_returns_none(self):
        # Arrange
        link: CategorizedLink = ("https://bandcamp.com/some-page",
                                 link_types.bandcamp)

        # Act
        result = getDescriptionParts(link)

        # Assert
        self.assertIsNone(result)

    def test_setAuthorLink_soundcloud(self):
        # Arrange
        mock_embed = MagicMock()

        # Act
        setAuthorLink(mock_embed, 'soundcloud')

        # Assert
        mock_embed.set_author.assert_called_once_with(
            name='SoundCloud',
            url='https://soundcloud.com/',
            icon_url='https://soundcloud.com/pwa-round-icon-192x192.png')

    def test_setAuthorLink_youtube(self):
        # Arrange
        mock_embed = MagicMock()

        # Act
        setAuthorLink(mock_embed, 'youtube')

        # Assert
        mock_embed.set_author.assert_called_once_with(
            name='YouTube',
            url='https://www.youtube.com/',
            icon_url=
            'https://www.youtube.com/s/desktop/0c61234c/img/favicon_144x144.png'
        )

    def test_setAuthorLink_youtubemusic(self):
        # Arrange
        mock_embed = MagicMock()

        # Act
        setAuthorLink(mock_embed, 'youtubemusic')

        # Assert
        mock_embed.set_author.assert_called_once_with(
            name='YouTube Music',
            url='https://music.youtube.com/',
            icon_url=
            'https://www.gstatic.com/youtube/media/ytm/images/applauncher/music_icon_144x144.png'
        )

    def test_setAuthorLink_spotify(self):
        # Arrange
        mock_embed = MagicMock()

        # Act
        setAuthorLink(mock_embed, 'spotify')

        # Assert
        mock_embed.set_author.assert_called_once_with(
            name='Spotify',
            url='https://open.spotify.com/',
            icon_url=
            'https://open.spotifycdn.com/cdn/images/icons/Spotify_256.17e41e58.png'
        )

    def test_setAuthorLink_bandcamp(self):
        # Arrange
        mock_embed = MagicMock()

        # Act
        setAuthorLink(mock_embed, 'bandcamp')

        # Assert
        mock_embed.set_author.assert_called_once_with(
            name='Bandcamp',
            url='https://bandcamp.com/',
            icon_url='https://s4.bcbits.com/img/favicon/favicon-32x32.png')

    def test_getUserIdFromFooter_valid(self):
        # Arrange
        mock_message = MagicMock()
        mock_embed = MagicMock()
        mock_embed.footer = MagicMock()
        mock_embed.footer.icon_url = "https://example.com/avatar.png#123456789"
        mock_message.embeds = [mock_embed]

        # Act
        result = getUserIdFromFooter(mock_message)

        # Assert
        self.assertEqual(result, 123456789)

    def test_getUserIdFromFooter_no_embeds(self):
        # Arrange
        mock_message = MagicMock()
        mock_message.embeds = []

        # Act
        result = getUserIdFromFooter(mock_message)

        # Assert
        self.assertIsNone(result)

    def test_getUserIdFromFooter_no_footer(self):
        # Arrange
        mock_message = MagicMock()
        mock_embed = MagicMock()
        mock_embed.footer = None
        mock_message.embeds = [mock_embed]

        # Act
        result = getUserIdFromFooter(mock_message)

        # Assert
        self.assertIsNone(result)

    def test_getUserIdFromFooter_invalid_format(self):
        # Arrange
        mock_message = MagicMock()
        mock_embed = MagicMock()
        mock_embed.footer = MagicMock()
        mock_embed.footer.icon_url = "https://example.com/avatar.png"
        mock_message.embeds = [mock_embed]

        # Act
        result = getUserIdFromFooter(mock_message)

        # Assert
        self.assertIsNone(result)

    @patch.dict('os.environ', {'EMOJI_ID': '123456789'})
    async def test_fetchEmbed_interaction_mode(self):
        # Mocking the message to contain a valid URL
        self.mock_message = AsyncMock()
        self.mock_message.content = "Check this out: https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        mock_bot = MagicMock()
        mock_bot.get_emoji.return_value = MagicMock()

        with patch('main.bot', mock_bot), \
             patch('main.getDescriptionParts') as mock_get_parts:
            mock_get_parts.return_value = {
                'title': 'Test Track',
                'embedPlatformType': 'soundcloud',
                'embedColour': 0xff5500,
                'description': 'Test Description'
            }

            # Act
            result = await fetchEmbed(self.mock_message, isInteraction=True)

            # Assert
            self.assertIsInstance(result, discord.Embed)
            self.assertEqual(result and result.title, 'Test Track')
            self.mock_message.add_reaction.assert_called_once()

    async def test_fetchEmbed_no_supported_embeds(self):
        # Arrange
        mock_message = MagicMock()
        mock_message.content = "https://example.com/not-supported"

        self.mock_message.channel.fetch_message.return_value = mock_message

        # Act & Assert
        with self.assertRaises(Exception) as context:
            await fetchEmbed(self.mock_message,
                             isInteraction=True,
                             isContext=True)

        self.assertIn("This message doesn't seem to contain a supported URL",
                      str(context.exception))


if __name__ == '__main__':
    unittest.main()
