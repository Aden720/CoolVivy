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
                'description':
                'Video description\n\nProvided to YouTube by Mock\nMock Artist · Mock Title\n\nMock Album\n\nReleased on: 2024-01-01\n',
                'uploadDate': '2024-01-01',
                'thumbnail': {
                    'thumbnails': [{
                        'url': 'https://example.com/thumb_alt.jpg'
                    }]
                }
            }
        }
    }
