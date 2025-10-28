# test_general_utils.py
import unittest

from general_utils import (
    cleanLinks,
    find_and_categorize_links,
    formatMillisecondsToDurationString,
    formatTimeToDisplay,
    formatTimeToTimestamp,
)
from object_types import link_types


class TestGeneralUtils(unittest.TestCase):

    def test_formatMillisecondsToDurationString(self):
        self.assertEqual(formatMillisecondsToDurationString(1000), '`0:01`')
        self.assertEqual(formatMillisecondsToDurationString(60000), '`1:00`')
        self.assertEqual(formatMillisecondsToDurationString(61000), '`1:01`')
        self.assertEqual(formatMillisecondsToDurationString(3599000),
                         '`59:59`')
        self.assertEqual(formatMillisecondsToDurationString(3600000),
                         '`1:00:00`')
        self.assertEqual(formatMillisecondsToDurationString(3661000),
                         '`1:01:01`')
        self.assertEqual(formatMillisecondsToDurationString(36000000),
                         '`10:00:00`')

    def test_formatTimeToDisplay_timestamp(self):
        self.assertEqual(
            formatTimeToDisplay('2013-03-02T03:01:22Z', '%Y-%m-%dT%H:%M:%SZ'),
            '2 March 2013')
        self.assertEqual(
            formatTimeToDisplay('2024-10-11T09:56:54Z', '%Y-%m-%dT%H:%M:%SZ'),
            '11 October 2024')
        self.assertEqual(
            formatTimeToDisplay('1999-01-21T00:41:44Z', '%Y-%m-%dT%H:%M:%SZ'),
            '21 January 1999')

    def test_formatTimeToDisplay_timestamp2(self):
        self.assertEqual(
            formatTimeToDisplay('2019-07-04T21:00:02', '%Y-%m-%dT%H:%M:%S'),
            '4 July 2019')
        self.assertEqual(
            formatTimeToDisplay('2022-04-01T12:33:09', '%Y-%m-%dT%H:%M:%S'),
            '1 April 2022')
        self.assertEqual(
            formatTimeToDisplay('2022-12-11T22:40:51', '%Y-%m-%dT%H:%M:%S'),
            '11 December 2022')

    def test_formatTimeToTimestamp(self):
        self.assertEqual(formatTimeToTimestamp('2019-04-04T21:00:02-07:00'),
                         '2019-04-04T21:00:02')
        self.assertEqual(formatTimeToTimestamp('2014-08-09T13:30:01+10:00'),
                         '2014-08-09T13:30:01')
        self.assertEqual(formatTimeToTimestamp('2015-10-09T06:30:22+0:00'),
                         '2015-10-09T06:30:22')

    def test_cleanLinks_single(self):
        self.assertEqual(
            cleanLinks('https://www.youtube.com/watch?v=dQw4w9WgXcQ'),
            '<https://www.youtube.com/watch?v=dQw4w9WgXcQ>')
        self.assertEqual(
            cleanLinks(
                'check out this soundcloud track https://soundcloud.com/hexagon/steve-hartz-like-home'
            ),
            'check out this soundcloud track <https://soundcloud.com/hexagon/steve-hartz-like-home>'
        )
        self.assertEqual(
            cleanLinks(
                "check out https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj"
                " on spotify"),
            "check out <https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj>"
            " on spotify")

    def test_cleanLinks_multiple(self):
        self.assertEqual(
            cleanLinks('''
            https://www.youtube.com/watch?v=dQw4w9WgXcQ
            https://soundcloud.com/hexagon/steve-hartz-like-home
            check out https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj on spotify
            instagram: https://www.instagram.com/p/Cj2J8k0n1fC/
            '''), '''
            <https://www.youtube.com/watch?v=dQw4w9WgXcQ>
            <https://soundcloud.com/hexagon/steve-hartz-like-home>
            check out <https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj> on spotify
            instagram: <https://www.instagram.com/p/Cj2J8k0n1fC/>
            ''')

    def test_find_and_categorize_links(self):
        message_content = ("""
            Check out this new release on SoundCloud https://on.soundcloud.com/someTrack
            and this music video on YouTube Music https://music.youtube.com/watch?v=dQw4w9WgXcQ.
            Also, listen to this album https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj
            and track https://artist.bandcamp.com/track/sample-track")
            """)

        categorized_links = find_and_categorize_links(message_content, True)
        self.assertEqual(
            categorized_links,
            [('https://on.soundcloud.com/someTrack', link_types.soundcloud),
             ('https://music.youtube.com/watch?v=dQw4w9WgXcQ',
              link_types.youtube),
             ('https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj',
              link_types.spotify),
             ('https://artist.bandcamp.com/track/sample-track',
              link_types.bandcamp)])

    def test_find_and_categorize_links_mobile_soundcloud(self):
        message_content = (
            "Check out this mobile link: "
            "https://m.soundcloud.com/mosscaofficial/wax-motif-taiki-nulight-w-scrufizzer-skank-n-flex-mossca-flipexclusive"
        )

        categorized_links = find_and_categorize_links(message_content, True)
        # Mobile URLs should be normalized to standard format
        self.assertEqual(
            categorized_links,
            [('https://soundcloud.com/mosscaofficial/wax-motif-taiki-nulight-w-scrufizzer-skank-n-flex-mossca-flipexclusive',
              link_types.soundcloud)])

    def test_find_and_categorize_links_www_soundcloud(self):
        message_content = (
            "Check out this www link: "
            "https://www.soundcloud.com/artist/track-name"
        )

        categorized_links = find_and_categorize_links(message_content, True)
        # WWW URLs should be normalized to standard format
        self.assertEqual(
            categorized_links,
            [('https://soundcloud.com/artist/track-name',
              link_types.soundcloud)])

    def test_find_and_categorize_links_standard_soundcloud(self):
        message_content = (
            "Standard SoundCloud link: "
            "https://soundcloud.com/artist/track-name"
        )

        categorized_links = find_and_categorize_links(message_content, True)
        # Standard URLs should remain unchanged
        self.assertEqual(
            categorized_links,
            [('https://soundcloud.com/artist/track-name',
              link_types.soundcloud)])

    def test_find_and_categorize_links_on_soundcloud(self):
        message_content = (
            "Short link: "
            "https://on.soundcloud.com/abc123"
        )

        categorized_links = find_and_categorize_links(message_content, True)
        # on.soundcloud.com URLs should remain unchanged
        self.assertEqual(
            categorized_links,
            [('https://on.soundcloud.com/abc123',
              link_types.soundcloud)])

    def test_find_and_categorize_links_soundcloud_url_normalization_comprehensive(
            self):
        message_content = ("""
            Mobile: https://m.soundcloud.com/artist1/track1
            WWW: https://www.soundcloud.com/artist2/track2
            Standard: https://soundcloud.com/artist3/track3
            Short: https://on.soundcloud.com/shortlink
            """)

        categorized_links = find_and_categorize_links(message_content, True)
        # Verify all variants are properly normalized or preserved
        self.assertEqual(categorized_links, [
            ('https://soundcloud.com/artist1/track1', link_types.soundcloud),
            ('https://soundcloud.com/artist2/track2', link_types.soundcloud),
            ('https://soundcloud.com/artist3/track3', link_types.soundcloud),
            ('https://on.soundcloud.com/shortlink', link_types.soundcloud)
        ])

    def test_find_and_categorize_links_ignore_angle_brackets_when_not_context_menu(
            self):
        message_content = ("""
            Check out this new release on SoundCloud https://on.soundcloud.com/someTrack
            and this music video <https://music.youtube.com/watch?v=dQw4w9WgXcQ>.
            Also, listen to this album https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj
            and track <https://artist.bandcamp.com/track/sample-track>
            """)

        # When isContextMenu is False, links in <> should be ignored
        categorized_links = find_and_categorize_links(message_content, False)
        self.assertEqual(
            categorized_links,
            [('https://on.soundcloud.com/someTrack', link_types.soundcloud),
             ('https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj',
              link_types.spotify)])

    def test_find_and_categorize_links_include_angle_brackets_when_is_context_menu(
            self):
        message_content = ("""
            Check out this new release on SoundCloud https://on.soundcloud.com/someTrack
            and this music video <https://music.youtube.com/watch?v=dQw4w9WgXcQ>.
            Also, listen to this album https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj
            and track <https://artist.bandcamp.com/track/sample-track>
            """)

        # When isContextMenu is True, all links should be included
        categorized_links = find_and_categorize_links(message_content, True)
        self.assertEqual(
            categorized_links,
            [('https://on.soundcloud.com/someTrack', link_types.soundcloud),
             ('https://music.youtube.com/watch?v=dQw4w9WgXcQ',
              link_types.youtube),
             ('https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj',
              link_types.spotify),
             ('https://artist.bandcamp.com/track/sample-track',
              link_types.bandcamp)])

    def test_find_and_categorize_links_mixed_angle_brackets(self):
        message_content = ("""
            Regular link: https://soundcloud.com/artist/track
            Link in brackets: <https://youtube.com/watch?v=test>
            Another regular: https://spotify.com/track/123
            Another in brackets: <https://bandcamp.com/album/test>
            """)

        # When isContextMenu is False, only regular links should be found
        categorized_links = find_and_categorize_links(message_content, False)
        self.assertEqual(
            categorized_links,
            [('https://soundcloud.com/artist/track', link_types.soundcloud),
             ('https://spotify.com/track/123', link_types.spotify)])

    def test_find_and_categorize_links_ignore_backticks_when_not_context_menu(
            self):
        message_content = ("""
            Check out this track: https://soundcloud.com/artist/regular-track
            Here's some code: `https://youtube.com/watch?v=code-example`
            And this album: https://spotify.com/album/regular-album
            ```
            Some code block with link:
            https://bandcamp.com/album/in-code-block
            ```
            """)

        # When isContextMenu is False, links in backticks should be ignored
        categorized_links = find_and_categorize_links(message_content, False)
        self.assertEqual(
            categorized_links,
            [('https://soundcloud.com/artist/regular-track',
              link_types.soundcloud),
             ('https://spotify.com/album/regular-album', link_types.spotify)])

    def test_find_and_categorize_links_include_backticks_when_is_context_menu(
            self):
        message_content = ("""
            Check out this track: https://soundcloud.com/artist/regular-track
            Here's some code: `https://youtube.com/watch?v=code-example`
            And this album: https://spotify.com/album/regular-album
            ```
            Some code block with link:
            https://bandcamp.com/album/in-code-block
            ```
            """)

        # When isContextMenu is True, all links should be included
        categorized_links = find_and_categorize_links(message_content, True)
        self.assertEqual(
            categorized_links,
            [('https://soundcloud.com/artist/regular-track',
              link_types.soundcloud),
             ('https://spotify.com/album/regular-album', link_types.spotify)])

    def test_find_and_categorize_links_mixed_filtering(self):
        message_content = ("""
            Regular: https://soundcloud.com/regular
            In angle brackets: <https://youtube.com/in-brackets>
            In backticks: `https://spotify.com/in-backticks`
            In code block:
            ```
            https://bandcamp.com/in-code-block
            ```
            Another regular: https://soundcloud.com/another-regular
            """)

        # When isContextMenu is False, only regular links should be found
        categorized_links = find_and_categorize_links(message_content, False)
        self.assertEqual(categorized_links, [
            ('https://soundcloud.com/regular', link_types.soundcloud),
            ('https://soundcloud.com/another-regular', link_types.soundcloud)
        ])
