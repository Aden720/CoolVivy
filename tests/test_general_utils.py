# test_general_utils.py
import unittest

from general_utils import (
    cleanLinks,
    formatMillisecondsToDurationString,
    formatTimeToDisplay,
    formatTimeToTimestamp,
)


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
                'check out https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj on spotify'
            ),
            'check out <https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj> on spotify'
        )

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



