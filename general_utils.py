import math
import re
from datetime import datetime


def formatMillisecondsToDurationString(milliseconds):
    (hours, seconds) = divmod(milliseconds / 1000, 3600)
    (minutes, seconds) = divmod(seconds, 60)
    minute_str = (f'{minutes:02.0f}' if minutes >= 10 or hours > 0
         else f'{minutes:1.0f}')
    timestamp = (f'{hours:.0f}:' if hours > 0 else
        '') + f'{minute_str}:{math.floor(seconds):02.0f}'
    return f'`{timestamp}`'


def formatTimeToDisplay(timestamp, timeFormat):
    datetimeObject = datetime.strptime(timestamp, timeFormat)
    return datetimeObject.strftime("%-d %B %Y")


def formatTimeToTimestamp(time):
    # Split the timestamp into the date-time part and the timezone part
    dateString, timezoneString = time.split('T')
    timeString, timezoneOffset = timezoneString.split(
        '-') if '-' in timezoneString else timezoneString.split('+')
    return dateString + 'T' + timeString


def cleanLinks(description):
    return re.sub(r'(https?:\/\/[a-zA-Z0-9\-\.]*[^\s]*)', r'<\1>',
         description)


def remove_trailing_slash(url):
    return re.sub(r'/$', '', url)


def find_and_categorize_links(message_content: str):
    # Define patterns for each platform including additional domains
    soundcloud_pattern = re.compile(r'https?://(?:www\.|on\.)?soundcloud\.com/[^\s]+')
    youtube_pattern = re.compile(r'https?://(?:www\.|music\.)?(?:youtube\.com|youtu\.be)/[^\s]+')
    spotify_pattern = re.compile(r'https?://(?:open\.)?spotify\.com/[^\s]+')
    bandcamp_pattern = re.compile(r'https?://[A-Za-z0-9_-]+\.bandcamp\.com/[^\s]+')

    # Initialize a list to store URLs with their platform types
    categorized_links = []

    # Find all URLs in the message
    urls = re.findall(r'https?://[^\s]+', message_content)

    # Determine the platform for each URL and maintain order
    for url in urls:
        if soundcloud_pattern.match(url):
            categorized_links.append((url, 'soundcloud'))
        elif youtube_pattern.match(url):
            categorized_links.append((url, 'youtube'))
        elif spotify_pattern.match(url):
            categorized_links.append((url, 'spotify'))
        elif bandcamp_pattern.match(url):
            categorized_links.append((url, 'bandcamp'))

    return categorized_links

# Example usage
message_content = (
    "Check out this new release on SoundCloud https://on.soundcloud.com/someTrack and this "
    "music video on YouTube Music https://music.youtube.com/watch?v=dQw4w9WgXcQ. "
    "Also, listen to this album https://open.spotify.com/album/37hp4WQU5PP4z5YclBFLdj "
    "and track https://artist.bandcamp.com/track/sample-track"
)

categorized_links = find_and_categorize_links(message_content)
for link, platform in categorized_links:
    print(f"Platform: {platform}, Link: {link}")
