import math
import re
from datetime import datetime
from typing import List

from object_types import CategorizedLink, link_types


def formatMillisecondsToDurationString(milliseconds):
    (hours, seconds) = divmod(milliseconds / 1000, 3600)
    (minutes, seconds) = divmod(seconds, 60)
    minute_str = (f'{minutes:02.0f}'
                  if minutes >= 10 or hours > 0 else f'{minutes:1.0f}')
    timestamp = (f'{hours:.0f}:' if hours > 0 else
                 '') + f'{minute_str}:{math.floor(seconds):02.0f}'
    return f'`{timestamp}`'


def formatTimeToDisplay(timestamp, timeFormat, outputFormat="%-d %B %Y"):
    datetimeObject = datetime.strptime(timestamp, timeFormat)
    return datetimeObject.strftime(outputFormat)


def formatTimeToTimestamp(time):
    # Split the timestamp into the date-time part and the timezone part
    dateString, timezoneString = time.split('T')
    timeString, timezoneOffset = timezoneString.split(
        '-') if '-' in timezoneString else timezoneString.split('+')
    return dateString + 'T' + timeString


def cleanLinks(description):
    return re.sub(r'(https?:\/\/[a-zA-Z0-9\-\.]*[^\s]*)', r'<\1>', description)


def remove_trailing_slash(url):
    return re.sub(r'/$', '', url)


def find_and_categorize_links(message_content: str) -> List[CategorizedLink]:
    # Define patterns for each platform including additional domains
    soundcloud_pattern = re.compile(
        r'https?://(?:www\.|on\.)?soundcloud\.com/[^\s]+')
    youtube_pattern = re.compile(
        r'https?://(?:www\.|music\.)?(?:youtube\.com|youtu\.be)/[^\s]+')
    spotify_pattern = re.compile(r'https?://(?:open\.)?spotify\.com/[^\s]+')
    bandcamp_pattern = re.compile(
        r'https?://[A-Za-z0-9_-]+\.bandcamp\.com/[^\s]+')

    # Initialize a list to store URLs with their platform types
    categorized_links = []

    # Find all URLs in the message
    urls = re.findall(r'https?://[^\s]+', message_content)
    cleaned_links = (link.rstrip('.")') for link in urls)

    # Determine the platform for each URL and maintain order
    for url in cleaned_links:
        if soundcloud_pattern.match(url):
            categorized_links.append((url, link_types.soundcloud))



def get_tag_content(soup, tag_name=None, attrs=None, property=None):
    """
    Safely get content from a BeautifulSoup tag with proper type checking.
    
    Args:
        soup: BeautifulSoup object
        tag_name: HTML tag name to find
        attrs: Dictionary of attributes to match
        property: Property attribute value (shorthand for {'property': value})
    
    Returns:
        str or None: The content attribute value if found and valid, None otherwise
    """
    from bs4 import Tag
    
    # Build search parameters
    search_params = {}
    if tag_name:
        search_params['name'] = tag_name
    if property:
        search_params['property'] = property
    if attrs:
        search_params['attrs'] = attrs
    
    # Find the tag
    tag = soup.find(**search_params)
    
    # Check if tag exists and is a valid Tag instance
    if tag and isinstance(tag, Tag):
        return tag.get('content')
    
    return None

        elif youtube_pattern.match(url):
            categorized_links.append((url, link_types.youtube))
        elif spotify_pattern.match(url):
            categorized_links.append((url, link_types.spotify))
        elif bandcamp_pattern.match(url):
            categorized_links.append((url, link_types.bandcamp))

    return categorized_links
