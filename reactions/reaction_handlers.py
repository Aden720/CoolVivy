from typing import List

import discord


async def fetch_animated_emotes(guild: discord.Guild) -> List[discord.Emoji]:
    """
    Fetches all custom animated emotes from a server.
    Args:
        guild (discord.Guild): The Discord server to fetch emotes from
    Returns:
        List[discord.Emoji]: List of animated emotes
    """
    animated_emotes = [emoji for emoji in guild.emojis if emoji.animated]
    return animated_emotes


class PaginatedSelect(discord.ui.View):

    def __init__(self, options, items_per_page=25, max_selections=20):
        super().__init__()
        self.originalMessage: discord.Message
        self.options = options
        self.current_page = 0
        self.items_per_page = items_per_page
        self.total_pages = -(-len(options) // items_per_page
                             )  # Ceiling division
        self.selected_emojis = set()
        self.max_selections = max_selections
        self.update_select_menu()

    def update_select_menu(self):
        # Clear existing items
        self.clear_items()

        # Calculate page bounds
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.options))

        # Create new select menu with current page's options
        page_options = self.options[start_idx:end_idx]
        if not page_options:
            select = discord.ui.Select(
                placeholder="No emotes available on this page",
                options=[
                    discord.SelectOption(label="No options", value="none")
                ],
                disabled=True)
        else:
            remaining = self.max_selections - len(self.selected_emojis)
            placeholder = f"Select emojis ({remaining} slots remaining)"
            if self.total_pages > 1:
                placeholder += f"\tPage {self.current_page + 1}/{self.total_pages}"
            select = discord.ui.Select(placeholder=placeholder,
                                       options=page_options,
                                       max_values=min(len(page_options),
                                                      remaining))

        async def select_callback(interaction: discord.Interaction):
            new_emojis = [
                next((opt.emoji
                      for opt in select.options if opt.value == value), None)
                for value in select.values
            ]
            new_emojis = [e for e in new_emojis if e]

            if len(self.selected_emojis) + len(
                    new_emojis) > self.max_selections:
                await interaction.response.send_message(
                    f"Cannot select more than {self.max_selections} emojis.",
                    ephemeral=True)
                return

            if interaction.message:
                for emoji in new_emojis:
                    try:
                        await self.originalMessage.add_reaction(emoji)
                        self.selected_emojis.update({emoji})
                    except discord.HTTPException as e:
                        pass
                        # if interaction.message.guild:
                        #     # Try to fetch the emoji from the server
                        #     emoji_id = str(emoji.id)
                        #     fetched_emoji = discord.utils.get(
                        #         interaction.message.guild.emojis,
                        #         id=int(emoji_id))
                        #     if fetched_emoji:
                        #         await self.originalMessage.add_reaction(
                        #             fetched_emoji)
                        #         self.selected_emojis.update({fetched_emoji})

            content = f"Selected: {' '.join(str(e) for e in self.selected_emojis)}"
            if len(self.selected_emojis) >= self.max_selections:
                content += "\nMaximum selections reached!"
                await interaction.response.edit_message(content=content,
                                                        view=None)
            else:
                self.update_select_menu()
                await interaction.response.edit_message(content=content,
                                                        view=self)

        select.callback = select_callback
        self.add_item(select)

        # Only add pagination buttons if there are multiple pages
        if self.total_pages > 1:
            # Previous button
            prev_button = discord.ui.Button(label="Previous",
                                            style=discord.ButtonStyle.gray,
                                            disabled=(self.current_page == 0))
            prev_button.callback = self.previous_page
            self.add_item(prev_button)

            # Next button
            next_button = discord.ui.Button(
                label="Next",
                style=discord.ButtonStyle.gray,
                disabled=(self.current_page == self.total_pages - 1))
            next_button.callback = self.next_page
            self.add_item(next_button)

        done_button = discord.ui.Button(label="Done",
                                        style=discord.ButtonStyle.primary)
        done_button.callback = self.done_interaction
        self.add_item(done_button)

    async def previous_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_select_menu()
            await interaction.response.edit_message(view=self)

    async def next_page(self, interaction: discord.Interaction):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_select_menu()
            await interaction.response.edit_message(view=self)

    async def done_interaction(self, interaction: discord.Interaction):
        content = (
            f"Added reactions: {' '.join(str(e) for e in self.selected_emojis)}"
            if len(self.selected_emojis) else "No reactions added.")
        await interaction.response.edit_message(content=content, view=None)
