import json
import os
import re

import discord
from discord.ext import commands

from bandcamp_utils import getBandcampParts
from general_utils import find_and_categorize_links, remove_trailing_slash
from object_types import CategorizedLink, link_types
from reactions import PaginatedSelect, fetch_animated_emotes
from soundcloud_utils import getSoundcloudParts
from spotify_utils import getSpotifyParts
from youtube_utils import getYouTubeParts

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

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
    print(f"Reaction detected: {reaction.emoji} from {user.name}")
    # Don't respond to bot reactions
    if user.bot or not bot.user:
        return

    message = reaction.message
    if (message.author.id == bot.user.id and user in message.mentions
            and message.reference):
        await message.delete()
    else:
        # Check if the bot has reacted to this message
        bot_reactions = [react for react in message.reactions if react.me]

        # If bot has reacted, check if the current reaction matches any bot reaction
        for bot_reaction in bot_reactions:
            if str(bot_reaction.emoji) == str(reaction.emoji):
                await bot_reaction.remove(bot.user)
                break


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
    if (message.reference and message.reference.resolved
            and message.reference.resolved.author.bot):
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


async def fetchEmbed(message,
                     isInteraction=False,
                     isDM=False,
                     isContext=False):
    webhook = None
    referencedUser = None
    embeds = []
    sentReplyMessage = False
    if not isInteraction and not isDM:
        webhook = await fetchWebhook(message)
        referencedUser = await getReferencedUser(message)
    canUseWebhook = webhook is not None

    allMusicUrls = find_and_categorize_links(message.content, isContext)

    if isContext and len(allMusicUrls) == 0:
        raise Exception(
            "This message doesn't seem to contain a supported URL.\nCurrently only "
            "Bandcamp, SoundCloud, Spotify and YouTube links are supported.")

    for link in allMusicUrls:
        #get all embed fields
        fieldParts = getDescriptionParts(link)
        if not fieldParts:
            raise Exception('No data found')

        #create a new embed
        embedVar = discord.Embed(title=fieldParts.get('title'),
                                 description=fieldParts.get('description'),
                                 color=fieldParts.get('embedColour', 0x00dcff),
                                 url=remove_trailing_slash(link[0]))

        #add platform link if applicable
        setAuthorLink(embedVar, fieldParts.get('embedPlatformType'))

        #thumbnail
        thumbnailUrl = fieldParts.get('thumbnailUrl')
        if thumbnailUrl:
            embedVar.set_thumbnail(url=thumbnailUrl)

        #populate embed fields
        for key, value in fieldParts.items():
            if key not in [
                    'description', 'title', 'thumbnailUrl',
                    'embedPlatformType', 'embedColour'
            ]:
                inline = key not in ['Tags', 'Description', 'Tracks', 'Videos']
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

    if canUseWebhook and len(embeds) > 0:
        # replace message content if the message is a reply
        if message.reference:
            jump_url = (message.reference.resolved.jump_url
                        if message.reference.resolved else
                        message.reference.jump_url)
            # try to mention the non-bot user
            if (not referencedUser and message.reference.resolved
                    and not message.reference.resolved.author.bot):
                referencedUser = message.reference.resolved.author
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


async def deleteOriginalInteractionMessage(interaction: discord.Interaction):
    # Delete the interaction response first
    try:
        await interaction.delete_original_response()
    except discord.NotFound:
        # Response was already deleted
        pass
    except discord.Forbidden:
        # Bot doesn't have permission to delete
        pass


def getDescriptionParts(link: CategorizedLink):
    linkType = link[1]
    linkUrl = link[0]
    if linkType == link_types.soundcloud:
        return getSoundcloudParts(linkUrl)
    elif linkType == link_types.youtube:
        return getYouTubeParts(linkUrl)
    elif linkType == link_types.spotify:
        return getSpotifyParts(linkUrl)
    else:  #Bandcamp
        if re.match('https?://bandcamp.com.+', linkUrl):
            return None
        return getBandcampParts(linkUrl)


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
    await interaction.response.defer(ephemeral=True)
    try:
        if message.author.id == interaction.user.id:
            await fetchEmbed(
                message, False,
                isinstance(interaction.channel, discord.DMChannel), True)
        else:
            trackEmbed = await fetchEmbed(message,
                                          isInteraction=True,
                                          isContext=True)
            if trackEmbed:
                await interaction.followup.send(
                    content=interaction.user.mention, embed=trackEmbed)
    except Exception as e:
        await interaction.followup.send(content=str(e), ephemeral=True)
    finally:
        await deleteOriginalInteractionMessage(interaction)


@bot.tree.context_menu(name="remove react")
async def remove_reactions_command(interaction: discord.Interaction,
                                   message: discord.Message):
    if not bot.user:
        return
    if not message.reactions:
        await interaction.response.send_message(
            "This message has no reactions.", ephemeral=True)
        return

    # Get all reactions by the bot

    bot_reactions = []
    for react in message.reactions:
        async for user in react.users():
            if user.id == bot.user.id:
                bot_reactions.append(react)
                break

    if not bot_reactions:
        await interaction.response.send_message(
            "No bot reactions found on this message.", ephemeral=True)
        return

    # Create select options for each bot reaction
    options = [
        discord.SelectOption(label=f"Remove {str(reaction.emoji.name)}",
                             value=str(reaction.emoji),
                             emoji=reaction.emoji)
        for reaction in bot_reactions
    ]

    # Create select menu
    select = discord.ui.Select(placeholder="Select reactions to remove...",
                               min_values=1,
                               max_values=len(options),
                               options=options)

    # Create view for the select menu
    view = discord.ui.View()

    async def select_callback(interaction: discord.Interaction):
        if not bot.user:
            return
        for emoji in select.values:
            await message.remove_reaction(emoji, bot.user)
        await interaction.response.edit_message(
            content=f"Removed {len(select.values)} reaction(s)", view=None)

    select.callback = select_callback
    view.add_item(select)

    await interaction.response.send_message("Select the reactions to remove:",
                                            view=view,
                                            ephemeral=True)


@bot.tree.context_menu(name="quick react (gif)")
async def quick_react_command(interaction: discord.Interaction,
                              message: discord.Message):
    if (testInstance == 'True' and str(interaction.user.id) != ownerUser):
        return

    #grab all the animated emojis in the server
    if interaction.guild is not None:
        emotes = await fetch_animated_emotes(interaction.guild)
        existing_reactions = {
            str(reaction.emoji)
            for reaction in message.reactions
        }
        remaining_slots = 20 - len(existing_reactions)

        if remaining_slots <= 0:
            await interaction.response.send_message(
                "This message already has the maximum number of reactions (20).",
                ephemeral=True)
            return

        # Filter out emotes that are already reacted
        available_emotes = [
            emote for emote in emotes if str(emote) not in existing_reactions
        ]

        if not available_emotes:
            await interaction.response.send_message(
                "No new emotes available to add.", ephemeral=True)
            return

        options = [
            discord.SelectOption(label=f"{emote.name}",
                                 emoji=emote,
                                 value=str(emote.id))
            for emote in available_emotes
        ]

        slots = min(len(available_emotes), remaining_slots)

        # Create the paginated view with remaining slots
        view = PaginatedSelect(options, max_selections=slots)
        view.originalMessage = message

        await interaction.response.send_message(
            f"Select emojis ({slots} slots remaining):",
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


if __name__ == "__main__":
    try:
        token = os.getenv("BOT_TOKEN") or ""
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
