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
        # Clear existing select menu
        for item in self.children[:]:
            if isinstance(item, discord.ui.Select):
                self.remove_item(item)

        # Calculate page bounds
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.options))

        # Create new select menu with current page's options
        select = discord.ui.Select(
            placeholder=
            f"Page {self.current_page + 1}/{self.total_pages} ({len(self.selected_emojis)}/{self.max_selections})",
            options=self.options[start_idx:end_idx],
            max_values=min(end_idx - start_idx,
                           self.max_selections - len(self.selected_emojis)))

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

            self.selected_emojis.update(new_emojis)

            if interaction.message:
                for emoji in new_emojis:
                    await self.originalMessage.add_reaction(emoji)

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

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
    async def previous_page(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_select_menu()
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_page(self, interaction: discord.Interaction,
                        button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_select_menu()
            await interaction.response.edit_message(view=self)
