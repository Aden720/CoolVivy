from typing import List, Optional, TypedDict


class SpotifyImage(TypedDict):
    url: str
    height: int
    width: int


class SpotifyArtist(TypedDict):
    name: str
    external_urls: dict[str, str]
    id: str


class SpotifyTracks(TypedDict):
    items: List['SpotifyTrack']  # Forward reference to SpotifyTrack
    total: int
    next: Optional[str]


class SpotifyAlbum(TypedDict):
    name: str
    artists: List[SpotifyArtist]
    images: List[SpotifyImage]
    release_date: str
    release_date_precision: str
    tracks: SpotifyTracks
    total_tracks: int
    external_urls: dict[str, str]
    label: Optional[str]


class SpotifyTrack(TypedDict):
    name: str
    artists: List[SpotifyArtist]
    album: SpotifyAlbum
    duration_ms: int
    external_urls: dict[str, str]
    track_number: int


class SpotifyPlaylistTrack(TypedDict):
    track: SpotifyTrack


class SpotifyPlaylistTracks(TypedDict):
    items: List[SpotifyPlaylistTrack]
    total: int
    next: Optional[str]


class SpotifyPlaylistOwner(TypedDict):
    display_name: str
    external_urls: dict[str, str]


class SpotifyPlaylist(TypedDict):
    name: str
    owner: SpotifyPlaylistOwner
    tracks: SpotifyPlaylistTracks
    images: List[SpotifyImage]
    followers: dict[str, int]
    description: Optional[str]
