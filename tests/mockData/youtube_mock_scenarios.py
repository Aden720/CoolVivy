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
            'musicVideoType': 'MUSIC_VIDEO_TYPE_ATV',
            'videoId': '123456789'
        },
        'microformat': {
            'microformatDataRenderer': {
                'pageOwnerDetails': {
                    'name': 'Mock Artist - Topic'
                },
                'description': ('Video description\n\n'
                                'Provided to YouTube by Mock\n'
                                'Mock Artist · Mock Title\n\n'
                                'Mock Album\n\n'
                                'Released on: 2024-01-01\n'),
                'uploadDate':
                '2020-10-29T03:07:04-07:00',
                'thumbnail': {
                    'thumbnails': [{
                        'url': 'https://example.com/thumb_alt.jpg'
                    }]
                }
            }
        }
    }
