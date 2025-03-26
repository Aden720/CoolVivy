import math
import re
from datetime import datetime


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


async def delete_message(message_id):
    message = find_message_by_id(message_id)
    if message:
        # Code to delete the message
        print(f"Message {message_id} deleted.")
    else:
        print(f"Message not found, couldn't delete.")


def find_message_by_id(message_id):
    # Logic to find and return the message by ID
    # Return None if not found
    return None  # Placeholder
