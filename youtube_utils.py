import re

from dotmap import DotMap
from ytmusicapi import YTMusic

from general_utils import (
    formatMillisecondsToDurationString,
    formatTimeToDisplay,
    formatTimeToTimestamp,
)

types = DotMap(track=1, playlist=2)


def fetchTrack(track_url):
    track, trackType = None, None
    ytmusic = YTMusic()
    videoId = re.search(r'watch\?v=([^&]*)', track_url) or re.search(
        'shorts/([^&]*)', track_url)
    if videoId is not None:
        videoId = videoId.group(1)
        track = ytmusic.get_song(videoId)
        trackType = types.track
    else:
        playlistId = re.search(r'playlist\?list=([^&]*)', track_url)
        if playlistId is not None:
            playlistId = playlistId.group(1)
            playlistId = ytmusic.get_album_browse_id(playlistId)
            if playlistId:
                track = ytmusic.get_album(playlistId)
                trackType = types.playlist
    return track, trackType


def getYouTubeParts(embed):
    youtubeParts = {'embedPlatformType': 'youtube', 'embedColour': 0xff0000}
    description = embed.description

    track, type = fetchTrack(embed.url)

    if track and type is types.track:
        #Title
        videoTitle = track['videoDetails']['title']
        if videoTitle:
            youtubeParts['title'] = videoTitle

        #Artist/Channel
        videoType = track['videoDetails'].get('musicVideoType')
        channelAuthor = track['microformat']['microformatDataRenderer'][
            'pageOwnerDetails']['name']
        musicAuthor = track['videoDetails']['author']
        author = musicAuthor
        if channelAuthor.endswith(
                ' - Topic') and channelAuthor != 'Release - Topic':
            channelAuthor = channelAuthor.replace(' - Topic', '')
            #Choose the longest artist name (the case for most scenarios)
            if len(channelAuthor) > len(musicAuthor):
                author = channelAuthor
        channelId = track['videoDetails']['channelId']
        isYoutubeMusicTrack = isYoutubeMusic(videoType)
        if isYoutubeMusicTrack:
            youtubeParts['embedPlatformType'] = 'youtubemusic'
            youtubeParts[
                'Artist'] = f'[{author}](https://music.youtube.com/channel/{channelId})'
        else:
            youtubeParts[
                'Channel'] = f'[{embed.author.name}]({embed.author.url})'

        #Duration
        videoDuration = track['videoDetails']['lengthSeconds']
        if videoDuration:
            youtubeParts['Duration'] = formatMillisecondsToDurationString(
                int(videoDuration) * 1000)

        #Description
        # videoDescription = track['microformat']['microformatDataRenderer'][
        #     'description']
        # if videoDescription:
        #     description = track['microformat']['microformatDataRenderer'][
        #         'description']

        #Square Thumbnail
        videoThumbnail = track['videoDetails']['thumbnail']['thumbnails'][-1]
        videoThumnailAlt = track['microformat']['microformatDataRenderer'][
            'thumbnail']['thumbnails'][0]
        youtubeParts['thumbnailUrl'] = (
            videoThumbnail['url'] if videoThumbnail['width']
            == videoThumbnail['height'] else videoThumnailAlt['url'])

    elif track and type is types.playlist:
        #youtube music playlist
        youtubeParts['embedPlatformType'] = 'youtubemusic'
        #Title
        albumTitle = track['title']
        if albumTitle:
            youtubeParts['title'] = albumTitle

        #Artists
        albumArtists = track['artists']
        youtubeParts[
            f'Artist{"s" if len(albumArtists) > 1 else ""}'] = ', '.join([
                f'[{artist["name"]}](https://music.youtube.com/channel/{artist["id"]})'
                for artist in albumArtists
            ])

        #Type
        albumType = track['type']
        if albumType:
            youtubeParts['Type'] = albumType

        #Tracks
        albumTrackCount = track['trackCount']
        if albumTrackCount:
            youtubeParts['Tracks'] = (f'{albumTrackCount} song'
                                      f'{"s" if albumTrackCount > 1 else ""}')

        #Duration
        albumDuration = track['duration_seconds']
        if albumDuration:
            youtubeParts['Duration'] = formatMillisecondsToDurationString(
                int(albumDuration) * 1000)

        #Released
        albumReleaseDate = track['year']
        if albumReleaseDate:
            youtubeParts['Released'] = formatTimeToDisplay(
                albumReleaseDate, '%Y')

        #Description
        albumDescription = track['description']
        if albumDescription:
            description = track['description']

        #Square Thumbnail
        youtubeParts['thumbnailUrl'] = track['thumbnails'][-1]['url']

    if description:
        descriptionMatch = re.search('.+?\n\n(.+?)\n.*Released on: (.*?)\n',
                                     description, re.S)
        if descriptionMatch:
            otherArtists = descriptionMatch.group(1).split(' · ')
            if len(otherArtists) > 2:
                otherArtists = otherArtists[2:]
                youtubeParts['Other Artists'] = ', '.join(otherArtists)
                #Reorder the fields
                temp = youtubeParts.pop('Duration')
                youtubeParts['Duration'] = temp

            youtubeParts['Released on'] = formatTimeToDisplay(
                descriptionMatch.group(2), '%Y-%m-%d')

    if not (youtubeParts.get('Released on')
            or youtubeParts.get('Released')) and track is not None:
        timestamp = formatTimeToTimestamp(
            track['microformat']['microformatDataRenderer']['uploadDate'])
        youtubeParts['Uploaded on'] = formatTimeToDisplay(
            timestamp, '%Y-%m-%dT%H:%M:%S')

    return youtubeParts


#Check if it's a Youtube Music track based on track type
def isYoutubeMusic(type):
    #MUSIC_VIDEO_TYPE_ATV
    #MUSIC_VIDEO_TYPE_OMV
    #MUSIC_VIDEO_TYPE_UGC
    #MUSIC_VIDEO_TYPE_OFFICIAL_SOURCE_MUSIC
    return type and type in ['MUSIC_VIDEO_TYPE_ATV', 'MUSIC_VIDEO_TYPE_OMV']
