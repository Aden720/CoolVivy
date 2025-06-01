
from typing import Tuple, Literal
from dotmap import DotMap

# Define the platform types
PlatformType = Literal['soundcloud', 'youtube', 'spotify', 'bandcamp']

# Define the tuple type for categorized links
LinkTuple = Tuple[str, PlatformType]

# Export link types for different platforms
link_types = DotMap(
    soundcloud='soundcloud',
    youtube='youtube', 
    spotify='spotify',
    bandcamp='bandcamp'
)
