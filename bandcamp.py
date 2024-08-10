import re
import os
import json
import requests
from bs4 import BeautifulSoup

endpoint = os.getenv('ENDPOINT')
if endpoint is None:
    raise Exception('Please set your endpoint in the Secrets pane.')


class Track:

    def __init__(self, title, artist, duration, year):
        self.title = title
        self.artist = artist
        self.duration = duration
        self.year = year


class Album:

    def __init__(self, title, artist, release_date, tracks):
        self.title = title
        self.artist = artist
        self.release_date = release_date
        self.tracks = tracks


class BandcampScraper:
    track_url_pattern = re.compile(
        r'https://(?:\w+\.)?bandcamp\.com/track/[\w-]+')
    album_url_pattern = re.compile(
        r'https://(?:\w+\.)?bandcamp\.com/album/[\w-]+')

    def __init__(self, url):
        track_url_pattern = re.compile(
            r'https://(?:\w+\.)?bandcamp\.com/track/[\w-]+')
        album_url_pattern = re.compile(
            r'https://(?:\w+\.)?bandcamp\.com/album/[\w-]+')
        data = self._fetch_data(url)
        if data is None:
            raise Exception("No data found")

        if re.match(track_url_pattern, url):
            self.track = self._parse_track(data)
            self.isTrack = True
            self.isAlbum = False
            #return Track(data)
        elif re.match(album_url_pattern, url):
            self.album = self._parse_album(data)
            self.isTrack = False
            self.isAlbum = True
            #return Album(data)

    @staticmethod
    def _parse_track(data):
        properties = data.get('additionalProperty')
        artistId = next(item['value'] for item in properties
                        if item['name'] == 'art_id')
        trackId = next(item['value'] for item in properties
                       if item['name'] == 'track_id')
        track = callAPI(artistId, trackId)
        return Track(data.get('title'), data.get('artist'),
                     data.get('duration'), data.get('year'))

    @staticmethod
    def _parse_album(data):
        return Album(data.get('title'), data.get('artist'),
                     data.get('duration'), data.get('year'))

    def _fetch_data(self, url):
        try:
            response = requests.get(url)
            if response.status_code != 200:
                response = requests.post(endpoint,
                                         data={
                                             'action': 'psvAjaxAction',
                                             'url': url,
                                         })
            if response.status_code != 200:
                return None
            else:
                soup = BeautifulSoup(response.content, 'html.parser')
                script_tag = soup.find('script',
                                       {'type': 'application/ld+json'})
                if script_tag is None:
                    return None
                else:
                    songData = json.loads(script_tag.text)
                    return songData
        except requests.exceptions.RequestException as e:
            print(f"Network error occurred: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

def getBandcampParts(embed):
    bandcampParts = {'embedPlatformType': 'bandcamp'}

    discography_page_pattern = re.compile(
        r'https://(?:\w+\.)?bandcamp\.com/music')
    if re.match(discography_page_pattern, embed.url):
        bandcampParts['description'] = 'Discography'
        return bandcampParts
    # try:
    #     scraper = BandcampScraper(embed.url)
    #     if scraper.isTrack:
    #         track = scraper.track
    #         return {
    #             'title': track.title,
    #             'artist': track.artist,
    #             'duration': track.duration,
    #             'year': track.year
    #         }
    #     elif scraper.isAlbum:
    #         album = scraper.album
    #         return {
    #             'title': album.title,
    #             'artist': album.artist,
    #             'release_date': album.release_date,
    #             'tracks': album.tracks
    #         }
    # except Exception as e:
    #     print(f"An error occurred: {e}")

    if True:

        channelUrl = re.sub(r'(https?://[a-zA-Z0-9\-]*\.bandcamp\.com).*',
                            r'\1', embed.url)
        if embed.title:
            embed.title, artist = embed.title.split(', by ')
            bandcampParts['Artist'] = artist
            if artist != 'Various Artists':
                embed.title = f'{artist} - {embed.title}'

        if embed.description:
            if embed.description.startswith('from the album'):
                bandcampParts['Album'] = embed.description.split(
                    'from the album ')[-1]
            elif embed.description.startswith('track by'):
                bandcampParts['description'] = 'Single'
            else:
                bandcampParts['description'] = embed.description

        if embed.provider:
            if embed.provider.name != bandcampParts.get('Artist'):
                bandcampParts['Channel'] = (
                    f'[{embed.provider.name}]'
                    f'({embed.provider.url or channelUrl})')
            else:
                bandcampParts[
                    'Artist'] = f'[{bandcampParts["Artist"]}]({channelUrl})'

        return bandcampParts


def callAPI(artistId, trackId):
    response = requests.get(
        url="https://bandcamp.com/api/mobile/25/tralbum_details?band_id=" +
        str(3074126532) + "&tralbum_id=" + str(1525250518) + "&tralbum_type=t")
    result = response.json()
