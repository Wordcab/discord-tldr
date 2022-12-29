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
import re
from datetime import datetime, timedelta
from pytimeparse import parse
from typing import Dict, List, Optional

import discord
from discord import app_commands

from wordcab import start_summary
from wordcab.core_objects import InMemorySource

from .database import bot_db


logger = logging.getLogger("discord")


MAX_CHARS = 4000
SUBSTITUTIONS = {
    "http\S+": "",  # Remove links
    "\\U0001f\S+": "",  # Remove emojis
    "<@\S+>": "",  # Remove mentions
    "<#\S+>": "",  # Remove channel mentions
    "“": "",  # Remove quotes
    "\n": " ",  # Replace newlines with spaces
    "\t": " ",  # Replace tabs with spaces
    " +": " ",  # Replace multiple spaces with a single space
    "^\s+|\s+$": "",  # Remove leading and trailing spaces
    "\u200b": "",  # Remove zero-width spaces
}
SUMMARY_SIZES = {"short": 1, "medium": 3, "long": 5}


@app_commands.command(name="summarize", description="Launch a Wordcab summarization job.")
@app_commands.rename(list_summarized_chat="include_chat")
@app_commands.rename(source_lang="language")
async def summarize(
    interaction: discord.Interaction,
    size: str,
    timeframe: str,
    list_summarized_chat: Optional[bool] = False,
    source_lang: Optional[str] = None,
) -> None:
    """
    Command that allow launching a Wordcab Summarization job.

    Parameters
    ----------
    interaction: discord.Interaction
        A Discord Interaction object.
    size: str,
        The size of the summary. Choose from `short`, `medium`, or `long`.
    timeframe: str
        The timeframe of the messages to summarize. e.g. `1w`, `3d`, `45min`, `2h30min`.
    list_summarized_chat: bool, default=False
        Whether to list the summarized chat in the response.
    source_lang: str, default=None
        The language of the source text. Choose from `de`, `en`, `es`, `fr`, and `it`. It's `en` by default.
    """
    if size not in SUMMARY_SIZES.keys():
        await interaction.response.send_message(
            "Invalid size. Choose from `short`, `medium`, and `long`.",
            ephemeral=True,
        )
    if source_lang is None:
        source_lang = "en"
    
    try:
        if not await bot_db.is_guild_authenticated(interaction.guild.id):
            await interaction.response.send_message(
                "This guild is not authenticated. Please run `/login` first.",
                ephemeral=True,
            )
        else:
            token = await bot_db.get_guild_token(interaction.guild.id)
            date = datetime.now() - timedelta(seconds=parse(timeframe))
            messages: List = []
            total_chars = 0
            async for msg in interaction.channel.history(after=date):
                if message_to_include(msg) and total_chars < MAX_CHARS:
                    messages.append(multiple_regex_replace(SUBSTITUTIONS, f"{msg.author}: {msg.content}"))
                    total_chars += len(msg.content)
            
            if total_chars == 0:
                await interaction.response.send_message(
                    "No messages to summarize.",
                    ephemeral=True,
                )
            elif total_chars < 1000:
                await interaction.response.send_message(
                    "Not enough messages to summarize.",
                    ephemeral=True,
                )
            else:
                source_object = InMemorySource(obj={"transcript": messages})
                display_name = f"{interaction.channel.name}_{interaction.guild.name}_{interaction.user.name}"
                summary_size = SUMMARY_SIZES[size]
                job = start_summary(
                    source_object=source_object,
                    display_name=display_name,
                    source_lang=source_lang,
                    summary_type="conversational",
                    summary_length=summary_size,
                    tags=[interaction.channel.name, interaction.guild.name, interaction.user.name],
                    api_key=token,
                )
                logger.info(
                    f"{interaction.user} - {interaction.guild}: summary of size {size} with {total_chars} chars launched."
                )
                if total_chars > 4000:
                    await interaction.response.send_message(
                        f"Summarization job launched: `{job.job_name}`\n\n"
                        "You should receive the summary in your DM soon! 👌\n\n"
                        "⚠️ To avoid summary alteration, the chats used for the summary has been truncated to 4000 characters.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"Summarization job launched: `{job.job_name}`\n\nYou should receive the summary in your DM soon! 👌",
                        ephemeral=True
                    )
                summarized_messages = messages if list_summarized_chat else None
                interaction.client.loop.create_task(
                    interaction.client.send_summary_as_dm(
                        interaction.guild,
                        interaction.user,
                        str(summary_size),
                        timeframe,
                        source_lang,
                        job.job_name,
                        token,
                        summarized_messages,
                    )
                )
    except Exception as e:
        logger.warning(f"Error while responding to interaction: {e}")
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)


def multiple_regex_replace(substitutions: Dict[str, str], text: str) -> str:
    """
    Replace multiple regex patterns in a string.

    Parameters
    ----------
    substitutions: Dict[str, str]
        A dictionary of regex patterns to replace.
    text: str
        The string to apply the replacements to.

    Returns
    -------
    str
        The string with the replacements applied.
    """
    regex = re.compile("(%s)" % "|".join(map(re.escape, substitutions.keys())))
    return regex.sub(lambda mo: substitutions[mo.string[mo.start() : mo.end()]], text)


def message_to_include(msg: discord.Message) -> bool:
    """
    Apply some filters to avoid unwanted messages to be included in the summary.
    
    Parameters
    ----------
    msg: discord.Message
        The message to check.
    
    Returns
    -------
    bool
        Whether the message should be included in the summary.
    """
    if not msg.author.bot and \
        msg.author and \
        msg.content and \
        not msg.content.startswith("/") and \
        len(msg.attachments) == 0 and \
        not msg.content.startswith("http") and \
        not msg.content.startswith("www"):
            return True
    else:
        return False
