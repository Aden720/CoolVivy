import re

from dotmap import DotMap
from ytmusicapi import YTMusic

from general_utils import (
    formatMillisecondsToDurationString,
    formatTimeToDisplay,
    formatTimeToTimestamp,
)

types = DotMap(track=1, album=2, playlist=3)


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
            track = ytmusic.get_playlist(playlistId)
            trackType = types.playlist
            if not track.get('duration'):
                albumBrowseId = ytmusic.get_album_browse_id(playlistId)
                if albumBrowseId:
                    track = ytmusic.get_album(albumBrowseId)
                    trackType = types.album
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
        videoDuration = getVideoDisplayDuration(track)
        if videoDuration:
            youtubeParts['Duration'] = videoDuration

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
    elif track and type is types.album:
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
        albumTrackCount = track['trackCount']
        albumType = track['type']
        youtubeParts['description'] = (
            f'{albumType} ({albumTrackCount} song{"s" if albumTrackCount > 1 else ""})'
            if albumType != 'Album' else f'{albumTrackCount} track album')

        #Tracks
        trackStrings = []
        trackSummaryCharLength = 0
        for trackEntry in track['tracks']:
            trackArtists = [artist['name'] for artist in trackEntry['artists']]
            artistString = formatArtistNames(trackArtists)
            trackTitle = f'{artistString} - {trackEntry["title"]}'
            trackUrl = f'https://music.youtube.com/watch?v={trackEntry["videoId"]}'
            trackDuration = f'`{trackEntry["duration"]}`'
            trackString = f'1. [{trackTitle}]({trackUrl}) {trackDuration}'

            trackStringLength = len(trackString) + 1
            if trackSummaryCharLength + trackStringLength <= 1000:
                trackStrings.append(trackString)
                trackSummaryCharLength += trackStringLength
            else:
                break

        youtubeParts['Tracks'] = '\n'.join(trackStrings)
        if len(trackStrings) != albumTrackCount:
            youtubeParts['Tracks'] += (
                f'\n...and {albumTrackCount - len(trackStrings)} more')

        #Duration
        youtubeParts['Duration'] = f'`{track["duration"]}`'

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
    elif track and type is types.playlist:
        totalVideos = track["trackCount"]
        youtubeParts['title'] = track['title']
        youtubeParts['description'] = f'Playlist ({totalVideos} videos)'
        youtubeParts['thumbnailUrl'] = track['thumbnails'][-1]['url']
        youtubeParts['Duration'] = f'`{track["duration"]}`'
        youtubeParts['Last updated'] = track['year']

        trackStrings = []
        trackSummaryCharLength = 0
        maxDisplayableTracksReached = False
        ytMusic = YTMusic()
        for trackEntry in track['tracks']:
            if maxDisplayableTracksReached:
                break
            if isYoutubeMusic(trackEntry['videoType']):
                trackArtists = [
                    artist['name'] for artist in trackEntry['artists']
                ]
                artistString = formatArtistNames(trackArtists)
                trackTitle = f'{artistString} - {trackEntry["title"]}'
                trackUrl = f'https://music.youtube.com/watch?v={trackEntry["videoId"]}'
            else:
                trackTitle = trackEntry['title']
                trackUrl = f'https://www.youtube.com/watch?v={trackEntry["videoId"]}'

            if not trackEntry.get('duration'):
                song = ytMusic.get_song(trackEntry['videoId'])
                trackDuration = getVideoDisplayDuration(song)
            else:
                trackDuration = f'`{trackEntry["duration"]}`'
            trackString = f'1. [{trackTitle}]({trackUrl}) {trackDuration}'

            trackStringLength = len(trackString) + 1
            if trackSummaryCharLength + trackStringLength <= 1000:
                trackStrings.append(trackString)
                trackSummaryCharLength += trackStringLength
            else:
                break
        youtubeParts['Videos'] = '\n'.join(trackStrings)
        if len(trackStrings) != totalVideos:
            youtubeParts['Videos'] += (
                f'\n...and {totalVideos - len(trackStrings)} more')

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

    if not (youtubeParts.get('Released on') or youtubeParts.get('Released')
            ) and track and type is not types.playlist:
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


def getVideoDisplayDuration(video):
    videoDuration = video['videoDetails']['lengthSeconds']
    return formatMillisecondsToDurationString(int(videoDuration) * 1000)


def formatArtistNames(artists):
    if not artists:
        return ""
    if len(artists) == 1:
        return artists[0]
    if len(artists) == 2:
        return f"{artists[0]} & {artists[1]}"
    return f"{', '.join(artists[:-1])} & {artists[-1]}"
