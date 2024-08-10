import re
import os
import json
import requests
from bs4 import BeautifulSoup

endpoint = os.getenv('ENDPOINT')
if endpoint is None:
    raise Exception(
        'Please set your endpoint in the Secrets pane.')

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
        return Track(data.get('title'), data.get('artist'),
                     data.get('duration'), data.get('year'))

    @staticmethod
    def _parse_album(data):
        return Album(data.get('title'), data.get('artist'),
                     data.get('duration'), data.get('year'))

    def _fetch_data(self, url):
        try:
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
