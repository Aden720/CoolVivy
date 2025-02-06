
def setupBasicVideo():
    return {
        'videoDetails': {
            'title': 'Mock Video Title',
            'author': 'Mock Artist',
            'channelId': 'UC123456789',
            'lengthSeconds': '180',
            'thumbnail': {
                'thumbnails': [{
                    'url': 'https://example.com/thumb.jpg',
                    'width': 120,
                    'height': 120
                }]
            },
            'musicVideoType': 'MUSIC_VIDEO_TYPE_ATV'
        },
        'microformat': {
            'microformatDataRenderer': {
                'pageOwnerDetails': {
                    'name': 'Mock Artist - Topic'
                },
                'description': 'Video description\n\nProvided to YouTube by Mock\nMock Artist · Mock Title\n\nMock Album\n\nReleased on: 2024-01-01\n',
                'uploadDate': '2024-01-01',
                'thumbnail': {
                    'thumbnails': [{
                        'url': 'https://example.com/thumb_alt.jpg'
                    }]
                }
            }
        }
    }

def setupBasicEmbed():
    class Author:
        def __init__(self):
            self.name = "Mock Channel"
            self.url = "https://youtube.com/channel/UC123456789"

    class Embed:
        def __init__(self):
            self.url = "https://www.youtube.com/watch?v=123456789"
            self.description = "Video description\n\nProvided to YouTube by Mock\nMock Artist · Mock Title\n\nMock Album\n\nReleased on: 2024-01-01\n"
            self.author = Author()

    return Embed()
