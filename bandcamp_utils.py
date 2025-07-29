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
    get_tag,
    get_tag_content,
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
types = DotMap(album='a', track='t', discography='d')


class Track:
    #map to track fields
    def __init__(self, pageData, trackData):
        self.trackUrl = pageData['@id']
        self.title = pageData['name']
        if pageData.get('keywords') and len(pageData.get('keywords')) > 3:
            self.tags = pageData['keywords'][1:-1]
        self.thumbnail = pageData['image']
        self.artist = {
            'name': pageData['byArtist']['name'],
            'url': pageData['byArtist'].get('@id')
        }
        self.release_date = pageData.get('datePublished', None)
        if self.release_date:
            self.release_date = datetime.strptime(
                self.release_date,
                '%d %b %Y %H:%M:%S GMT').replace(tzinfo=timezone.utc)

        albumArtist = pageData['inAlbum'].get('byArtist')
        if albumArtist and 'name' in albumArtist and albumArtist.get('name'):
            artistName = albumArtist.get('name')
            if artistName != self.artist['name'] and artistName not in [
                    'Various', 'Various Artists'
            ]:
                self.artist = {
                    'name': artistName,
                    'url': albumArtist.get('@id')
                }
        self.publisher = {
            'name': pageData['publisher']['name'],
            'url': pageData['publisher'].get('@id')
        }
        numTracks = pageData['inAlbum'].get(
            'numTracks', 2)  #this data seems to only be returned for singles
        if numTracks > 1:
            self.album = {
                'name': pageData['inAlbum']['name'],
                'url': pageData['inAlbum'].get('@id')
            }

        #change the artist if the track is from a different artist
        if checkTrackTitle(
                self.title) and self.artist and self.artist.get('name'):
            if (self.publisher and self.publisher.get('name')
                    and self.publisher['name'] in self.artist['name']):
                setTrackTitle(self)
            else:
                trackTitleParts = getTrackTitleParts(self.title)
                if trackTitleParts and trackTitleParts.group(
                        1) == self.artist['name']:
                    self.title = trackTitleParts.group(2)
        #extra data from API
        if trackData:
            self.is_purchasable = trackData['is_purchasable']
            self.free_download = trackData['free_download']
            self.price = trackData['price']
            self.currency = trackData['currency']
            self.duration = trackData['tracks'][0]['duration']
            self.release_date = datetime.fromtimestamp(
                trackData['release_date'], tz=timezone.utc)
            if trackData.get('tags') and len(trackData.get('tags')) > 0:
                self.tags = (tag['name'] for tag in trackData['tags'])

    def mapToParts(self):
        parts = {}
        if self.thumbnail:
            parts['thumbnailUrl'] = self.thumbnail
        parts['title'] = (self.title if self.artist['name'].lower()
                          in self.title.lower() else self.artist['name'] +
                          ' - ' + self.title)
        parts['Duration'] = formatMillisecondsToDurationString(self.duration *
                                                               1000)
        if self.is_purchasable:
            parts['Price'] = (
                f'`{format_currency(self.price, self.currency, locale="en_US")}`'
            ) if self.price > 0 else f'[Free]({self.trackUrl})'
        elif self.free_download:
            parts['Price'] = f':arrow_down: [Free Download]({self.trackUrl})'

        if self.release_date:
            displayTime = formatTimeToDisplay(
                self.release_date.strftime('%Y-%m-%dT%H:%M:%S'),
                '%Y-%m-%dT%H:%M:%S')
            if self.release_date > datetime.now(timezone.utc):
                parts['Releases on'] = displayTime
            else:
                parts['Released on'] = displayTime
        if self.artist:
            parts['Artist'] = (f'[{self.artist["name"]}]({self.artist["url"]})'
                               if self.artist.get('url') else
                               self.artist['name'])
            if artistIsMultipleArtists(self.artist["name"]):
                parts['Artists'] = parts['Artist']
                parts['title'] = (self.title if self.artist["name"]
                                  == 'Various Artists' else
                                  self.artist['name'] + ' - ' + self.title)
                parts.pop('Artist')
        if hasattr(self, 'album'):
            parts['Album'] = (f'[{self.album["name"]}]({self.album["url"]})'
                              if self.album.get('url') else self.album['name'])
        if self.publisher and self.publisher['name'] != self.artist['name']:
            parts[
                'Channel'] = f'[{self.publisher["name"]}]({self.publisher["url"]})'
        formatted_tags = getFormattedTags(self)
        if formatted_tags:
            parts['Tags'] = formatted_tags
        return parts


class Album:
    #map to album fields
    def __init__(self, pageData, albumData):
        self.title = pageData['name']
        self.thumbnail = pageData['image']
        self.albumUrl = pageData['@id']
        self.num_tracks = pageData['numTracks']
        self.tracks = pageData['track']['itemListElement']
        self.tracksData = albumData['tracks']
        self.release_date = datetime.strptime(
            pageData['datePublished'],
            '%d %b %Y %H:%M:%S GMT').replace(tzinfo=timezone.utc)
        if pageData.get('keywords') and len(pageData.get('keywords')) > 3:
            self.tags = pageData['keywords'][1:-1]

        self.artist = {
            'name': pageData['byArtist']['name'],
            'url': pageData['byArtist'].get('@id')
        }
        self.publisher = {
            'name': pageData['publisher']['name'],
            'url': pageData['publisher'].get('@id')
        }

        self.is_purchasable = None
        self.price = None
        self.currency = None
        self.free_download = None

        #extra data from API
        if albumData:
            self.is_purchasable = albumData['is_purchasable']
            self.free_download = albumData['free_download']
            self.price = albumData['price']
            self.currency = albumData['currency']
            if albumData.get('tags') and len(albumData.get('tags')) > 0:
                self.tags = (tag['name'] for tag in albumData['tags'])
            self.release_date = datetime.fromtimestamp(
                albumData['release_date'], tz=timezone.utc)

    def mapToParts(self):
        parts = {}
        if self.thumbnail:
            parts['thumbnailUrl'] = self.thumbnail
        parts['title'] = self.title
        parts['description'] = f'{self.num_tracks} track album'
        trackStrings = []
        trackSummaryCharLength = 0
        artists = {self.artist['name']}
        totalDuration = 0
        maxDisplayableTracksReached = False
        for track, trackData in zip(self.tracks, self.tracksData):
            durationMs = 0
            if trackData['duration'] is not None:
                durationMs = trackData['duration'] * 1000
                totalDuration += durationMs
            if checkTrackTitle(trackData['title']):
                trackNameRegex = r"(.+?)\s[-–]\s(.*)"
                match = re.match(trackNameRegex, trackData['title'])
                if match:
                    trackData['title'] = match.group(2)
                    trackData['band_name'] = match.group(1)
            if not maxDisplayableTracksReached:
                trackString = (
                    f'{trackData["track_num"]}. ' +
                    (f'[{trackData["band_name"]} - {trackData["title"]}]'
                     if trackData['band_name'].lower() != self.artist['name'].
                     lower() else f'[{trackData["title"]}]') +
                    #map the url from page
                    f'({track["item"].get("@id")})' +
                    (f' `{formatMillisecondsToDurationString(durationMs)}`'
                     if durationMs > 0 else ""))
                trackStringLength = len(trackString) + 1
                if trackSummaryCharLength + trackStringLength <= 1000:
                    trackStrings.append(trackString)
                    trackSummaryCharLength += trackStringLength
                else:
                    maxDisplayableTracksReached = True
            if self.artist['name'].lower() not in trackData['band_name'].lower(
            ):
                artists.add(trackData['band_name'])

        parts['Duration'] = formatMillisecondsToDurationString(totalDuration)
        if self.is_purchasable and self.price and self.currency:
            parts['Price'] = (
                f'`{format_currency(self.price, self.currency, locale="en_US")}`'
                if self.price > 0 else f'[Free]({self.albumUrl})')
        elif self.free_download:
            parts['Price'] = f':arrow_down: [Free Download]({self.albumUrl})'
        if self.release_date:
            displayTime = formatTimeToDisplay(
                self.release_date.strftime('%Y-%m-%dT%H:%M:%S'),
                '%Y-%m-%dT%H:%M:%S')
            if self.release_date > datetime.now(timezone.utc):
                parts['Releases on'] = displayTime
            else:
                parts['Released on'] = displayTime
        if len(artists) > 1 or self.artist['name'] == 'Various Artists':
            parts['title'] = self.title
            parts['Artist'] = 'Various Artists'
        else:
            parts['title'] = f'{self.artist["name"]} - {self.title}'
            parts['Artist'] = (f'[{self.artist["name"]}]({self.artist["url"]})'
                               if self.artist.get('url') else
                               self.artist['name'])

        if artistIsMultipleArtists(parts['Artist']):
            parts['Artists'] = parts['Artist']
            parts.pop('Artist')

        if self.publisher['name'] != self.artist['name']:
            parts['Channel'] = (f'[{self.publisher["name"]}]'
                                f'({self.publisher["url"]})')

        parts['Tracks'] = '\n'.join(trackStrings)
        if len(trackStrings) != self.num_tracks:
            parts[
                'Tracks'] += f'\n...and {self.num_tracks - len(trackStrings)} more'

        formatted_tags = getFormattedTags(self)
        if formatted_tags:
            parts['Tags'] = formatted_tags

        return parts


class Discography:
    #map to album fields
    def __init__(self, properties):
        self.title = properties.get('title')
        self.thumbnail = properties.get('imageUrl')
        self.description = properties.get('description')
        self.location = properties.get('location')

    def mapToParts(self):
        parts = {}
        parts['title'] = self.title
        parts['description'] = (
            'Discography\n\n'
            f'{self.description if self.description else ""}')
        parts['thumbnailUrl'] = self.thumbnail
        if self.location:
            parts['Location'] = self.location
        return parts


class BandcampScraper:

    def __init__(self, url: str):

        isDiscography = bool(re.match(discography_page_pattern, url))
        data = self._fetch_data(url, isDiscography)
        if data is None:
            raise Exception("No data found")

        if isDiscography:
            self.dataClass = self._parse_discography(data)
            self.dataType = types.discography
        elif re.match(track_url_pattern, url):
            self.dataClass = self._parse_track(data)
            self.dataType = types.track
        elif re.match(album_url_pattern, url):
            self.dataClass = self._parse_album(data)
            self.dataType = types.album

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

    @staticmethod
    def _parse_discography(soup: BeautifulSoup):
        imageUrl = get_tag_content(soup, property='og:image')
        title = get_tag_content(soup, attrs={'name': 'title'})
        description = get_tag_content(soup, property='og:description')
        band_name_location = get_tag(soup, id='band-name-location')
        location = (get_tag_content(
            band_name_location, attrs={'class': 'location'}, asString=True)
                    if band_name_location else None)
        properties = {
            'title': title,
            'imageUrl': imageUrl,
            'description': description,
            'location': location
        }
        return Discography(properties)

    def _fetch_data(self, url, pageData=False):
        try:
            response = requests.get(url)
            if response.status_code != 200 and endpoint:
                response = requests.post(endpoint,
                                         data={
                                             'action': 'psvAjaxAction',
                                             'url': url,
                                         })
            if response.status_code != 200:
                return None
            else:
                soup = BeautifulSoup(response.content, 'html.parser')
                if pageData:
                    return soup
                else:
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


def getBandcampParts(url: str):
    bandcampParts = {'embedPlatformType': 'bandcamp', 'embedColour': 0x1da0c3}

    #fetches the data from the bandcamp url
    try:
        # raise Exception('bypassing until mapping is complete')
        scraper = BandcampScraper(remove_trailing_slash(url))
        if scraper.dataClass:
            bandcampParts.update(scraper.dataClass.mapToParts())
    except Exception as e:
        #fallback method from embed
        print(f"An error occurred while fetching Bandcamp details: {e}")

    return bandcampParts


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


def checkTrackTitle(track_title):
    return '-' in track_title or '–' in track_title


def getTrackTitleParts(title):
    # Skip matching if the title has format "title (artist - edit)"
    if re.search(r"\([^)]*[-–][^)]*\)$", title):
        return None
    trackNameRegex = r"(.+?)\s[-–]\s(.*)"
    return re.match(trackNameRegex, title)


def setTrackTitle(track: Track):
    match = getTrackTitleParts(track.title)
    if match:
        track.title = match.group(2)
        track.artist = {'name': match.group(1), 'url': None}


def getFormattedTags(track):
    if hasattr(track, 'tags'):
        formatted_tags = [f'`{tag}`' for tag in track.tags]
        return ', '.join(formatted_tags)


def artistIsMultipleArtists(artistString):
    if artistString == 'Various Artists':
        return True
    artist_parts_comma = artistString.split(', ')
    artist_parts_ampersand = artistString.split(' & ')
    return len(artist_parts_comma) > 1 or len(artist_parts_ampersand) > 1
