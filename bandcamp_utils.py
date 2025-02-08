import json
import os
import re
from datetime import datetime, timezone

import requests
from babel.numbers import format_currency
from bs4 import BeautifulSoup
from dotmap import DotMap

from general_utils import (
    formatMillisecondsToDurationString,
    formatTimeToDisplay,
    remove_trailing_slash,
)

endpoint = os.getenv('ENDPOINT')
if endpoint is None:
    raise Exception('Please set your endpoint in the Secrets pane.')

track_url_pattern = re.compile(
    r'https://[A-Za-z0-9_-]+\.bandcamp\.com/track/[A-Za-z0-9_-]+')
album_url_pattern = re.compile(
    r'https://[A-Za-z0-9_-]+\.bandcamp\.com/album/[A-Za-z0-9_-]+')
discography_page_pattern = re.compile(
    r'https://[A-Za-z0-9_-]+\.bandcamp\.com/music')
types = DotMap(album='a', track='t')


class Track:
    #map to track fields
    def __init__(self, pageData, trackData):
        self.trackUrl = pageData['@id']
        self.title = pageData['name']
        self.tags = pageData['keywords']
        self.thumbnail = pageData['image']
        self.artist = {
            'name': pageData['byArtist']['name'],
            'url': pageData['byArtist'].get('@id')
        }
        self.publisher = {
            'name': pageData['publisher']['name'],
            'url': pageData['publisher'].get('@id')
        }
        self.album = {
            'name': pageData['inAlbum']['name'],
            'url': pageData['inAlbum'].get('@id')
        }

        #extra data from API
        if trackData:
            self.free_download = trackData['free_download']
            if len(trackData['tags']) > 0:
                self.tags = trackData['tags']
            self.currency = trackData['currency']
            self.price = trackData['price']
            self.is_purchasable = trackData['is_purchasable']
            self.duration = trackData['tracks'][0]['duration']
            self.release_date = trackData['release_date']

    def mapToParts(self):
        parts = {}
        if self.thumbnail:
            parts['thumbnailUrl'] = self.thumbnail
        parts['title'] = self.artist['name'] + ' - ' + self.title
        parts['Duration'] = formatMillisecondsToDurationString(self.duration *
                                                               1000)
        if self.is_purchasable:
            parts['Price'] = (
                f'`{format_currency(self.price, self.currency, locale="en_US")}`'
            )
        elif self.free_download:
            parts['Price'] = f'`:arrow_down: [Free Download]({self.trackUrl})`'
        if self.release_date:
            release_date = datetime.fromtimestamp(self.release_date,
                                                  tz=timezone.utc)
            parts['Released on'] = formatTimeToDisplay(
                release_date.strftime('%Y-%m-%dT%H:%M:%S'),
                '%Y-%m-%dT%H:%M:%S')
        if self.artist:
            parts['Artist'] = (f'[{self.artist["name"]}]({self.artist["url"]})'
                               if self.artist['url'] else self.artist['name'])
        if self.album:
            parts['Album'] = (f'[{self.album["name"]}]({self.album["url"]})'
                              if self.album['url'] else self.album['name'])
        if self.publisher and self.publisher['name'] != self.artist['name']:
            parts[
                'Channel'] = f'[{self.publisher["name"]}]({self.publisher["url"]})'
        if self.tags and len(self.tags) > 0:
            formatted_tags = [f'`{tag}`' for tag in self.tags]
            parts['Tags'] = ', '.join(formatted_tags)
        return parts


class Album:

    #map to album fields
    def __init__(self, pageData, albumData):
        self.title = pageData['name']
        self.artist = pageData['byArtist']['name']
        self.num_tracks = pageData['numTracks']
        self.tracks = pageData['track']['itemListElement']
        self.release_date = formatTimeToDisplay(pageData['datePublished'],
                                                '%d %b %Y %H:%M:%S GMT')
        self.tags = pageData['keywords']
        self.publisher = {
            'name': pageData['publisher']['name'],
            'url': pageData['publisher'].get('@id')
        }

        #extra data from API
        if albumData:
            self.release_date = albumData
            self.tracks = albumData['tracks']
            self.release_date = datetime.fromtimestamp(
                albumData['release_date'],
                tz=timezone.utc).strftime('%-d %B %Y')
            if len(albumData['tags']) > 0:
                self.tags = albumData['tags']

    def mapToParts(self):
        parts = {}
        parts['title'] = self.title
        trackStrings = []
        artists = {self.artist}
        totalDuration = 0
        for track in self.tracks:
            durationMs = track["duration"] * 1000
            totalDuration += durationMs
            trackStrings.append(
                f'{track["track_num"]}. [{track["band_name"]} - {track["title"]}]'
                #map the url from page
                #f'({track[url?]})'
                f' `{formatMillisecondsToDurationString(durationMs)}`')
            artists.add(track['band_name'])

        if len(artists) > 1 or self.artist == 'Various Artists':
            parts['title'] = self.title
            parts['Artist'] = 'Various Artists'
        else:
            parts['title'] = f'{self.artist} - {self.title}'
            parts['Artist'] = self.artist

        if self.publisher['name'] != parts['Artist']:
            parts['Channel'] = (f'[{self.publisher["name"]}]'
                                f'({self.publisher["url"]})')
        else:
            parts['Artist'] = f'[{self.artist}]({self.publisher["url"]})'

        return parts


class BandcampScraper:

    def __init__(self, url):
        data = self._fetch_data(url)
        if data is None:
            raise Exception("No data found")

        if re.match(track_url_pattern, url):
            self.track = self._parse_track(data)
            self.isTrack = True
            self.isAlbum = False
            # return Track(data)
        elif re.match(album_url_pattern, url):
            self.album = self._parse_album(data)
            self.isTrack = False
            self.isAlbum = True
            #return Album(data)

    @staticmethod
    def _parse_track(pageData):
        properties = {
            item['name']: item['value']
            for item in pageData['additionalProperty']
        }
        artistId = properties.get('art_id')
        trackId = properties.get('track_id')
        trackData = callAPI(artistId, trackId, types.track)
        return Track(pageData, trackData)

    @staticmethod
    def _parse_album(pageData):
        properties = {
            item['name']: item['value']
            for item in pageData['albumRelease'][0]['additionalProperty']
        }
        artistId = properties.get('art_id')
        albumId = properties.get('item_id')
        albumData = callAPI(artistId, albumId, types.album)
        return Album(pageData, albumData)

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
    bandcampParts = {'embedPlatformType': 'bandcamp', 'embedColour': 0x1da0c3}

    if re.match(discography_page_pattern, embed.url):
        bandcampParts['title'] = embed.provider.name
        bandcampParts['description'] = 'Discography'
        return bandcampParts

    #fetches the data from the bandcamp url
    try:
        # raise Exception('bypassing until mapping is complete')
        scraper = BandcampScraper(remove_trailing_slash(embed.url))
        if scraper.isTrack:
            track = scraper.track
            bandcampParts.update(track.mapToParts())
        elif scraper.isAlbum:
            album = scraper.album
            bandcampParts.update(album.mapToParts())
    except Exception as e:
        #fallback method from embed
        print(f"An error occurred: {e}")
        bandcampParts.update(getPartsFromEmbed(embed))

    return bandcampParts


#get track details from embed
def getPartsFromEmbed(embed):
    trackParts = {}
    channelUrl = re.sub(r'(https?://[a-zA-Z0-9\-]*\.bandcamp\.com).*', r'\1',
                        embed.url)
    if embed.title:
        trackParts['title'], artist = embed.title.split(', by ')
        trackParts['Artist'] = artist
        if artist != 'Various Artists' and artist not in trackParts["title"]:
            title_artist_pattern = re.compile(r'^.+\s-\s.+$')
            #channel name may not always be artist
            if not title_artist_pattern.match(embed.title):
                trackParts['title'] = f'{artist} - {trackParts["title"]}'
            artistString = trackParts['title'].split(' - ')[0]
            artist_parts_comma = artistString.split(', ')
            artist_parts_ampersand = artistString.split(' & ')
            if len(artist_parts_comma) > 1 or len(artist_parts_ampersand) > 1:
                trackParts['Artists'] = artistString
                trackParts.pop('Artist', None)
            else:
                trackParts['Artist'] = artistString

    if embed.description:
        if embed.description.startswith('from the album'):
            trackParts['Album'] = embed.description.split(
                'from the album ')[-1]
        elif embed.description.startswith('track by'):
            trackParts['description'] = 'Single'
        else:
            trackParts['title'] = trackParts['title'].split(' - ')[-1]
            trackParts['description'] = embed.description

    if embed.provider:
        if embed.provider.name != trackParts.get('Artist'):
            trackParts['Channel'] = (f'[{embed.provider.name}]'
                                     f'({embed.provider.url or channelUrl})')
        else:
            trackParts['Artist'] = f'[{trackParts["Artist"]}]({channelUrl})'

    return trackParts


def callAPI(artistId, itemId, type):
    try:
        response = requests.get(url=(
            f'https://bandcamp.com/api/mobile/25/tralbum_details'
            f'?band_id={artistId}&tralbum_id={itemId}&tralbum_type={type}'))
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
