import asyncio
import json
import os
import re

import discord
from discord import app_commands
from discord.ext import commands

from bandcamp_utils import getBandcampParts
from general_utils import remove_trailing_slash
from reactions import PaginatedSelect, fetch_animated_emotes
from soundcloud_utils import getSoundcloudParts
from spotify_utils import getSpotifyParts
from youtube_utils import getYouTubeParts

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ownerUser = str(os.getenv("OWNER_USER_ID"))
testInstance = os.getenv("TEST_INSTANCE", "False")
servers = os.getenv("SERVERS")
if servers:
    server_whitelist = json.loads(servers)
else:
    server_whitelist = []
    print("SERVERS is not set in the environment variables.")


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    # Sync commands to make sure they are registered
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')


@bot.event
async def on_guild_join(guild):
    # Find a text channel to send the welcome message
    if guild.system_channel is not None:
        to_send = guild.system_channel
    else:
        # Use the first channel the bot has permissions to send messages in
        to_send = discord.utils.find(
            lambda x: x.permissions_for(guild.me).send_messages,
            guild.text_channels)
    # Message content
    join_message = f"Hello {guild.name}!\nThanks for inviting me [❤︎](https://i.imgur.com/fFvOiry.png).\n"\
        "Use `/help` for the basic instructions."
    # Send the message
    if to_send:
        await to_send.send(join_message)


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    # Don't respond to bot reactions
    if user.bot:
        return
        
    # You can check for specific emoji reactions here
    if str(reaction.emoji) == "👍":
        await reaction.message.channel.send(f"{user.name} gave a thumbs up!")

@bot.event
async def on_message(message):
    if message.author.bot is True \
        or (testInstance == "True" and str(message.author.id) != ownerUser):# or \
        #(testInstance == 'False' and str(message.author.id) == ownerUser):
        return
    elif bot.user and (str(bot.user.id) in message.content):
        if 'hello' in message.content.lower():
            await message.channel.send('Hello!')
        else:
            await message.channel.send(
                f'Ask <@{ownerUser}> for help.'
                if ownerUser else 'Use **/help** for help.')
    elif message.guild and str(message.guild.id) in server_whitelist:
        await asyncio.sleep(3)
        try:
            await fetchEmbed(message, False)
        except Exception as e:
            print(f'Error: {e}')
    else:
        referencedUser = await getReferencedUser(message)
        if referencedUser:
            await message.reply(referencedUser.mention, mention_author=False)


# If the message is a reply to the bot's message,
# get the replied message and fetch the original user
async def getReferencedUser(message):
    if message.reference and message.reference.resolved.author.bot:
        referencedUserId = getUserIdFromFooter(message.reference.resolved)
        if referencedUserId and referencedUserId != message.author.id:
            referencedUser = await message.guild.fetch_member(referencedUserId)
            if referencedUser:
                hasMentionedUserInMessage = referencedUser.mention in message.content
                if not hasMentionedUserInMessage:
                    return referencedUser
    return None


async def fetchWebhook(message):
    # Check if the bot has the correct permissions to manage webhooks
    canSend = message.channel.permissions_for(message.guild.me).manage_webhooks
    if not canSend:
        await message.author.send(
            "I do not have permission to manage webhooks!\n"
            "Ask the server owners to give me the permission to manage webhooks"
            " so I can send less cluttered messages to the channel.")
        return None
    # Create a webhook
    webhook = None
    channel = message.channel.parent if hasattr(message.channel,
                                                'parent') else message.channel
    webhooks = await channel.webhooks()
    if len(webhooks) > 0:
        for hook in webhooks:
            if hook.token is not None:
                webhook = hook
                break

    if webhook is None:
        webhook = await channel.create_webhook(name='CoolVivy embed')

    return webhook


async def fetchEmbed(message, isInteraction=False, isDM=False):
    newMessage = await message.channel.fetch_message(message.id)
    embeds = []
    webhook = None
    referencedUser = None
    sentReplyMessage = False
    if not isInteraction and not isDM:
        webhook = await fetchWebhook(message)
        referencedUser = await getReferencedUser(message)
    canUseWebhook = webhook is not None

    for embed in newMessage.embeds:
        if any(
                word in embed.url for word in
            ['soundcloud.com', 'youtube.com', 'spotify.com', 'bandcamp.com']):
            #get all embed fields
            fieldParts = getDescriptionParts(embed)
            if not fieldParts:
                raise Exception('No data found')

            #create a new embed
            embedVar = discord.Embed(
                title=fieldParts.get('title', embed.title),
                description=fieldParts.get('description'),
                color=fieldParts.get('embedColour', 0x00dcff),
                url=remove_trailing_slash(embed.url))

            #add platform link if applicable
            setAuthorLink(embedVar, fieldParts.get('embedPlatformType'))

            #thumbnail
            thumbnailUrl = fieldParts.get('thumbnailUrl')
            if thumbnailUrl:
                embedVar.set_thumbnail(url=thumbnailUrl)
            elif embed.thumbnail:
                embedVar.set_thumbnail(url=embed.thumbnail.url)

            #populate embed fields
            for key, value in fieldParts.items():
                if key not in [
                        'description', 'title', 'thumbnailUrl',
                        'embedPlatformType', 'embedColour'
                ]:
                    inline = key not in [
                        'Tags', 'Description', 'Tracks', 'Videos'
                    ]
                    embedVar.add_field(name=key, value=value, inline=inline)

            #remove embed from original message
            if not isInteraction and fieldParts.get(
                    'embedPlatformType') == 'bandcamp':
                await message.edit(suppress=True)

            #react to message
            if isInteraction:
                emoji_id = os.getenv("EMOJI_ID")
                emoji = bot.get_emoji(int(emoji_id)) if emoji_id else '🔗'
                await message.add_reaction(emoji)

            #send embed
            if isInteraction:
                return embedVar
            else:
                if canUseWebhook:
                    embeds.append(embedVar)
                    continue
                if referencedUser:
                    await message.reference.resolved.reply(embed=embedVar)
                    sentReplyMessage = True
                else:
                    await message.reply(embed=embedVar)
        else:
            if isInteraction:
                raise Exception(
                    "This doesn't seem to be a supported URL.\nCurrently only "
                    "Bandcamp, SoundCloud, Spotify and YouTube are supported.")
    if canUseWebhook and len(embeds) > 0:
        # replace message content if the message is a reply
        if message.reference:
            jump_url = message.reference.resolved.jump_url
            message.content = (
                f'{referencedUser.mention if referencedUser else ""} {jump_url}\n'
                f'{message.content}')
        embeds[-1].set_footer(
            text='Powered by CoolVivy',
            icon_url=
            f'{message.channel.guild.me.avatar.url}#{message.author.id}')
        if hasattr(message.channel, 'parent'):
            await webhook.send(content=message.content,
                               embeds=embeds,
                               username=message.author.display_name,
                               avatar_url=message.author.avatar.url,
                               thread=message.channel)
        else:
            await webhook.send(
                content=message.content,
                embeds=embeds,
                username=message.author.display_name,
                avatar_url=message.author.avatar.url,
            )
        sentReplyMessage = True
        #remove original message
        await message.delete()
    if not sentReplyMessage and referencedUser:
        await message.reply(referencedUser.mention, mention_author=False)


def getDescriptionParts(embed):
    if 'soundcloud.com' in embed.url:
        return getSoundcloudParts(embed)
    elif 'youtube.com' in embed.url:
        return getYouTubeParts(embed)
    elif 'spotify.com' in embed.url:
        return getSpotifyParts(embed)
    else:  #Bandcamp
        if re.match('https?://bandcamp.com.+', embed.url):
            return None
        return getBandcampParts(embed)


def setAuthorLink(embedMessage, embedType):
    if embedType == 'soundcloud':
        embedMessage.set_author(
            name='SoundCloud',
            url='https://soundcloud.com/',
            icon_url='https://soundcloud.com/pwa-round-icon-192x192.png')
    elif embedType == 'youtube':
        embedMessage.set_author(
            name='YouTube',
            url='https://www.youtube.com/',
            icon_url=
            'https://www.youtube.com/s/desktop/0c61234c/img/favicon_144x144.png'
        )
    elif embedType == 'youtubemusic':
        embedMessage.set_author(
            name='YouTube Music',
            url='https://music.youtube.com/',
            icon_url=
            'https://www.gstatic.com/youtube/media/ytm/images/applauncher/music_icon_144x144.png'
        )
    elif embedType == 'spotify':
        embedMessage.set_author(
            name='Spotify',
            url='https://open.spotify.com/',
            icon_url=
            'https://open.spotifycdn.com/cdn/images/icons/Spotify_256.17e41e58.png'
        )
    else:
        embedMessage.set_author(
            name='Bandcamp',
            url='https://bandcamp.com/',
            icon_url='https://s4.bcbits.com/img/favicon/favicon-32x32.png')


def getUserIdFromFooter(message):
    if len(message.embeds) > 0:
        footer = message.embeds[-1].footer
        if footer and footer.icon_url:
            # Regex to match 'iconURL#126532652625'
            powered_by_vivy_regex = re.compile(r".*#(\d+)")
            match = powered_by_vivy_regex.search(str(footer.icon_url))
            if match and match.group(1):
                return int(match.group(1))
    return None


#Allow user to delete a message related to them or the bot, for cleanup
@bot.tree.context_menu(name='delete message')
async def delete_bot_message(interaction: discord.Interaction,
                             message: discord.Message):
    # if (testInstance == 'True' and str(interaction.user.id) != user2):  # or (
    #     #testInstance == 'False' and str(interaction.user.id) == user2):
    #     return
    try:
        canDelete = False
        if (bot.user and message.author.id == bot.user.id) or \
           (message.author.id == interaction.user.id):
            canDelete = True
        elif message.author.bot is True:
            userId = getUserIdFromFooter(message)
            # check the user id matches
            if userId == interaction.user.id:
                canDelete = True
        if canDelete:
            await message.delete()
            # await interaction.response.send_message(content='Attempting to delete...',
            #     ephemeral=True)
            await interaction.response.send_message(content='Message deleted',
                                                    ephemeral=True)
        else:
            await interaction.response.send_message(
                content=
                '''This message is not from me or a reformatted message from you.
                I can only delete messages from me or posted by you.''',
                ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(content=str(e), ephemeral=True)


# Define a context menu for getting embed metadata
@bot.tree.context_menu(name='get track metadata')
async def fetch_embed_message(interaction: discord.Interaction,
                              message: discord.Message):
    if (testInstance == 'True'
            and str(interaction.user.id) != ownerUser):  # or (
        #testInstance == 'False' and str(interaction.user.id) == user2):
        return
    await interaction.response.send_message(
        content=f'Fetching details for {message.jump_url}', ephemeral=True)
    try:
        if message.author.id == interaction.user.id:
            await fetchEmbed(
                message, False,
                isinstance(interaction.channel, discord.DMChannel))
        else:
            trackEmbed = await fetchEmbed(message, True)
            if trackEmbed:
                await interaction.followup.send(
                    content=interaction.user.mention, embed=trackEmbed)
    except Exception as e:
        await interaction.followup.send(content=str(e), ephemeral=True)


@bot.tree.context_menu(name="example")
async def example_command(interaction: discord.Interaction,
                          message: discord.Message):
    if (testInstance == 'True' and str(interaction.user.id) != ownerUser):
        return
    # Create a list of options (example with 50 options)
    if interaction.guild is not None:
        emotes = await fetch_animated_emotes(interaction.guild)
        options = [
            discord.SelectOption(label=f"{emote.name}",
                               emoji=emote,
                               value=str(emote.id)) for emote in emotes
        ]

        # Create the paginated view (25 items per page)
        view = PaginatedSelect(options)
        view.originalMessage = message

        await interaction.response.send_message("Select an option:",
                                                view=view,
                                                ephemeral=True)


@bot.tree.command(name="help", description="Show help information")
async def help_command(interaction: discord.Interaction):
    help_text = """I provide information about track links and albums.

__**How to use**__
On any track link from Soundcloud, Spotify, Bandcamp or YouTube:
1. Right click/hold a message
1. Select **Apps**
1. Select **get track metadata**.
    - You can clean up messages I've sent by selecting the **delete message** option.
    """.strip()
    await interaction.response.send_message(help_text, ephemeral=True)


try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("Please add your token to the Secrets pane.")
    bot.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        print(
            "The Discord servers denied the connection for making too many requests"
        )
        print(
            "Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests"
        )
    else:
        raise e
