# Copyright 2022 The Wordcab Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

import discord
from discord import app_commands

from wordcab.login import _check_valid_credentials

from .database import bot_db


logger = logging.getLogger("discord")


class Login(discord.ui.Modal, title="Log in to Wordcab"):
    """Login modal view for logging in to Wordcab."""

    email = discord.ui.TextInput(
        label="Wordcab account email",
        placeholder="Enter your email...",
        required=True,
    )
    api_token = discord.ui.TextInput(
        label="Wordcab API token",
        placeholder="Enter your API token...",
        required=True,
        style=discord.TextStyle.long,
        max_length=100,
    )


    async def on_submit(self, interaction: discord.Interaction):
        """On submit."""
        valid = _check_valid_credentials(self.email.value, self.api_token.value)
        if not valid:
            await interaction.response.send_message(
                "❌ Invalid credentials.",
                ephemeral=True,
            )
        else:
            guild_id = await bot_db.get_a_guild_id(interaction.guild.id)
            if guild_id is None:
                await interaction.response.send_message("❌ Guild not found.", ephemeral=True)
            await bot_db.authenticate_a_guild(guild_id=guild_id, email=self.email.value, token=self.api_token.value)
            await interaction.response.send_message(f"✅ Authenticated {self.email.value}!", ephemeral=True)


    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(f"Error: {error}", ephemeral=True)


class Logout(discord.ui.View):
    """Logout view."""

    def __init__(self):
        super().__init__(timeout=30.0)
        self.value = None


    @discord.ui.button(label="Log out", style=discord.ButtonStyle.red)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm button."""
        await bot_db.unauthenticate_a_guild(interaction.guild.id)
        await interaction.response.send_message("✅ Server Logged out!", ephemeral=True)
        self.value = True
        self.stop()


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction,  button: discord.ui.Button):
        """Cancel button."""
        await interaction.response.send_message("❌ Cancelled.", ephemeral=True)
        self.value = False
        self.stop()


@app_commands.command(name="worcab-login", description="Log in to Wordcab.")
async def login(interaction: discord.Interaction):
    """Login command."""
    await interaction.response.send_modal(Login())


@app_commands.command(name="wordcab-logout", description="Log out of Wordcab.")
async def logout(interaction: discord.Interaction):
    """Logout command."""
    is_guild_authenticated = await bot_db.is_guild_authenticated(interaction.guild.id)
    if not is_guild_authenticated:
        await interaction.response.send_message("❌ Guild not logged in. You can log in with `/login`.", ephemeral=True)
    else:
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ You are not the guild owner.", ephemeral=True)
        else:
            view = Logout()
            await interaction.response.send_message("Are you sure you want to log out?", view=view)
            await view.wait()
            if view.value:
                logger.info(f"Guild {interaction.guild} logged out from Wordcab.")
            else:
                logger.info(f"Guild {interaction.guild} cancelled logout from Wordcab.")
            view.clear_items()
