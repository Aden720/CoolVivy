class Embed:

  def __init__(self):
    self.url = ''
    self.title = ''
    self.provider = {}


def setupBasicEmbed():
  embed = Embed()
  embed.url = 'https://artist.bandcamp.com/track/song-title'
  embed.title = 'Song Title, by Artist Name'
  embed.provider.name = 'Artist Name'
  embed.provider.url = 'https://artist.bandcamp.com'
  embed.description = 'from the album Album Name'
  return embed


def setupAlbumEmbed():
  embed = type('', (), {})()
  embed.url = 'https://artist.bandcamp.com/album/album-title'
  embed.title = 'Album Title, by Artist Name'
  embed.provider = type('', (), {})()
  embed.provider.name = 'Artist Name'
  embed.provider.url = 'https://artist.bandcamp.com'
  return embed


def setupDiscographyEmbed():
  embed = type('', (), {})()
  embed.url = 'https://artist.bandcamp.com/music'
  embed.provider = type('', (), {})()
  embed.provider.name = 'Artist Name'
  return embed
