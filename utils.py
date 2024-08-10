import math


def formatMillisecondsToDurationString(milliseconds):
             (hours, seconds) = divmod(milliseconds / 1000, 3600)
             (minutes, seconds) = divmod(seconds, 60)
             timestamp = (f'{hours:02.0f}:' if hours > 0 else
                          '') + f'{minutes:02.0f}:{math.floor(seconds):02.0f}'
             return f'`{timestamp}`'
