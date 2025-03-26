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

    def __init__(self, options, items_per_page=25):
        super().__init__()
        self.options = options
        self.current_page = 0
        self.items_per_page = items_per_page
        self.total_pages = -(-len(options) // items_per_page
                             )  # Ceiling division
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
            placeholder=f"Page {self.current_page + 1}/{self.total_pages}",
            options=self.options[start_idx:end_idx])
        
        async def select_callback(interaction: discord.Interaction):
            selected_value = select.values[0]
            await interaction.message.delete()
            await interaction.response.send_message(f"You selected: {selected_value}", ephemeral=True)
            
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
