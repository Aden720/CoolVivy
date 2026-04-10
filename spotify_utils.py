import logging
import re
from typing import Optional

from spotapi.album import PublicAlbum
from spotapi.public import Public

from general_utils import formatMillisecondsToDurationString, formatTimeToDisplay

logger = logging.getLogger(__name__)


def _spotify_url(uri: str) -> str:
    parts = uri.split(':')
    if len(parts) == 3:
        return f'https://open.spotify.com/{parts[1]}/{parts[2]}'
    return ''


def _extract_id(url: str, kind: str) -> Optional[str]:
    m = re.search(rf'/{kind}/([A-Za-z0-9]+)', url)
    return m.group(1) if m else None


def _cover_url(cover_art: dict) -> str:
    sources = cover_art.get('sources', [])
    if not sources:
        return ''
    return max(sources, key=lambda s: s.get('height', 0)).get('url', '')


def _format_date(date_obj: dict) -> str:
    precision = date_obj.get('precision', 'YEAR')
    iso = date_obj.get('isoString', '')
    if precision == 'DAY':
        return formatTimeToDisplay(iso[:10], '%Y-%m-%d')
    elif precision == 'MONTH':
        return formatTimeToDisplay(iso[:7], '%Y-%m', '%B %Y')
    else:
        return str(date_obj.get('year', iso[:4]))


def _track_artists(track_union: dict) -> list:
    first = track_union.get('firstArtist', {}).get('items', [])
    other = track_union.get('otherArtists', {}).get('items', [])
    return first + other


def _artist_link(artist: dict) -> str:
    name = artist.get('profile', {}).get('name', '')
    url = _spotify_url(artist.get('uri', ''))
    return f'[{name}]({url})' if url else name


def _format_artist_string(artists: list) -> str:
    return ', '.join(_artist_link(a) for a in artists)


def _title_artist_names(artists: list, title: str) -> str:
    return ', '.join(
        a.get('profile', {}).get('name', '')
        for a in artists
        if a.get('profile', {}).get('name', '') not in title
    )


def reformatTitle(title: str) -> str:
    remix_regex = r"(.+?)\s[-–]\s(.*?(Remix|Mix|Edit).*)"
    if re.match(remix_regex, title):
        title = re.sub(remix_regex, r'\1 (\2)', title)
    return title


def getSpotifyParts(url: str) -> dict:
    parts = {'embedPlatformType': 'spotify', 'embedColour': 0x1db954}
    try:
        if '/track/' in url and 'open.spotify.com' in url:
            track_id = _extract_id(url, 'track')
            if not track_id:
                raise ValueError('Could not extract track ID')
            _build_track_parts(parts, track_id)
        elif '/album/' in url and 'open.spotify.com' in url:
            album_id = _extract_id(url, 'album')
            if not album_id:
                raise ValueError('Could not extract album ID')
            _build_album_parts(parts, album_id)
    except Exception as e:
        logger.error('Error fetching Spotify details: %s', e)
    return parts


def _build_track_parts(parts: dict, track_id: str) -> None:
    info = Public.song_info(track_id)
    if not info:
        raise ValueError('No data returned')
    track = info['data']['trackUnion']

    title = track['name']
    artists = _track_artists(track)
    album = track['albumOfTrack']

    parts['Duration'] = formatMillisecondsToDurationString(
        track['duration']['totalMilliseconds'])

    parts['Released'] = _format_date(album['date'])

    cover = _cover_url(album.get('coverArt', {}))
    if cover:
        parts['thumbnailUrl'] = cover

    artist_str = _format_artist_string(artists)
    title_artists = _title_artist_names(artists, title)

    if len(artists) > 1:
        parts['Artists'] = artist_str
    else:
        parts['Artist'] = artist_str

    total_tracks = album.get('tracks', {}).get('totalCount', 0)
    if total_tracks > 1:
        album_url = _spotify_url(album.get('uri', ''))
        parts['Album'] = f'[{album["name"]}]({album_url})'

    title = reformatTitle(title)
    parts['title'] = f'{title_artists} - {title}' if title_artists else title


def _build_album_parts(parts: dict, album_id: str) -> None:
    info = PublicAlbum(album_id).get_album_info()
    if not info:
        raise ValueError('No data returned')
    album = info['data']['albumUnion']

    title = album['name']
    artists = album.get('artists', {}).get('items', [])
    track_items = album.get('tracksV2', {}).get('items', [])
    total_tracks = album.get('tracksV2', {}).get('totalCount', 0)

    artist_str = _format_artist_string(artists)
    title_artists = _title_artist_names(artists, title)

    track_strings = []
    track_char_len = 0
    total_duration = 0
    max_reached = False

    for item in track_items:
        t = item['track']
        total_duration += t.get('duration', {}).get('totalMilliseconds', 0)
        if not max_reached:
            track_title = reformatTitle(t.get('name', ''))
            track_artists_list = t.get('artists', {}).get('items', [])
            track_artist_names = ', '.join(
                a['profile']['name'] for a in track_artists_list
                if a['profile']['name'] not in title_artists
            )
            track_url = _spotify_url(t.get('uri', ''))
            display = (f'[{track_artist_names} - {track_title}]'
                       if track_artist_names and track_artist_names != title_artists
                       else f'[{track_title}]')
            track_str = (
                f'{t["trackNumber"]}. {display}({track_url})'
                f' {formatMillisecondsToDurationString(t.get("duration", {}).get("totalMilliseconds", 0))}'
            )
            if track_char_len + len(track_str) + 1 <= 1000:
                track_strings.append(track_str)
                track_char_len += len(track_str) + 1
            else:
                max_reached = True

    if total_tracks > 1:
        parts['Duration'] = formatMillisecondsToDurationString(total_duration)
    else:
        single_ms = track_items[0]['track'].get('duration', {}).get('totalMilliseconds', 0) if track_items else 0
        parts['Duration'] = formatMillisecondsToDurationString(single_ms)

    parts['Released'] = _format_date(album['date'])

    cover = _cover_url(album.get('coverArt', {}))
    if cover:
        parts['thumbnailUrl'] = cover

    if len(artists) > 1:
        parts['Artists'] = artist_str
    elif artists and artists[0]['profile']['name'] == 'Various Artists':
        parts['Artists'] = 'Various Artists'
    else:
        parts['Artist'] = artist_str

    if album.get('label'):
        parts['Label'] = album['label']

    if total_tracks > 1:
        parts['description'] = f'{total_tracks} track album'
        parts['Tracks'] = '\n'.join(track_strings)
        if len(track_strings) != total_tracks:
            parts['Tracks'] += f'\n...and {total_tracks - len(track_strings)} more'

    parts['title'] = (
        f'{title_artists} - {title}'
        if title_artists and title_artists != 'Various Artists'
        else title
    )
