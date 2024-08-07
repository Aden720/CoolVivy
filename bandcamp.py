from urllib import request
import requests

from bs4 import BeautifulSoup


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

    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
        }
        self.session.headers.update(self.headers)

    def fetch_track(self, url):
        response = self.session.get(url)
        if response.status_code == 403:
            raise Exception(
                "Access forbidden. You might need to set proper headers.")

        soup = BeautifulSoup(response.content, 'html.parser')
        script_tag = soup.find('script', {'type': 'application/ld+json'})
        # title = soup.find('meta', property='og:title')['content']
        # artist = soup.find('meta', property='og:site_name')['content']
        # duration = soup.find('span', class_='time').text
        # year = soup.find('meta', itemprop='datePublished')['content'][:4]
        # return Track(title, artist, duration, year)

    def fetch_album(self, url):
        response = self.session.get(url)
        if response.status_code == 403:
            raise Exception(
                "Access forbidden. You might need to set proper headers.")

        soup = BeautifulSoup(response.content, 'html.parser')

        # Parse album metadata here (similar to fetch_track)

        tracks = []
        track_elements = soup.find_all('div', class_='track_list_item')
        for track_elem in track_elements:
            track_url = track_elem.find('a')['href']
            # Complete track URL assuming relative path
            full_track_url = f'https://{band}.bandcamp.com{track_url}'
            track = self.fetch_track(full_track_url)
            tracks.append(track)
        return Album(title, artist, release_date, tracks)
