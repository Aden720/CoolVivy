# CoolVivy Discord Bot - Music sharing

This is a starting point for making your own Discord bot using Python and the [discordpy](https://discordpy.readthedocs.io/) library.
Read [their getting-started guides](https://discordpy.readthedocs.io/en/stable/#getting-started) to get the most out of this template.

## Getting Started

To get set up, you'll need to follow [these bot account setup instructions](https://discordpy.readthedocs.io/en/stable/discord.html),
and then copy the token for your bot and added it as a secret with the key of `BOT_TOKEN` in the "Secrets (Environment variables)" panel.

### Environment Secrets

#### Initialized in main.py
- `BOT_TOKEN`: This is the bot token used to authenticate and run your Discord bot. It allows your bot to connect to the Discord API and perform perform its functions.

- `OWNER_USER_ID`: Used to identify the owner user or administrator within your bot, possibly for restricting certain commands or features to this user.
  
- `TEST_INSTANCE`: A flag to specify whether the current running instance is meant for testing, affecting how the bot behaves or logs actions. Used in conjunction with the OWNER_USER_ID to limit impact of core functions when running simultaneous instances.

- `SERVERS`: This environment stores JSON data related to configuration of a whitelist of servers the bot is allowed to operate some features in.
    - e.g. '["serverID","16568721763","58635398573"]'

#### Initialized in spotify_utils.py
- `SPOTIFY_CLIENT_ID`: This is the client ID for the Spotify API. It's used to authenticate requests made to the Spotify service, enabling the bot to interact with Spotify's features.

- `SPOTIFY_CLIENT_SECRET`: This is the client secret for the Spotify API, used together with the client ID for secure authentication.

#### Used in youtube_utils.py
- `YOUTUBE_CLIENT_ID`: This is the client ID of your Google Cloud Console project client.
- `YOUTUBE_CLIENT_SECRET`: This is the client secret for the YoutubeData API. Follow the instructions at https://ytmusicapi.readthedocs.io/en/stable/setup/oauth.html for more details.

## FAQ

If you get the following error message while trying to start the server: `429 Too Many Requests` (accompanied by a lot of HTML code), 
try the advice given in this Stackoverflow question:
https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests