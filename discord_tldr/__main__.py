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

import asyncio
import logging
import logging.handlers
import os
from aiohttp import ClientSession
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from wordcab import delete_job, retrieve_job, retrieve_summary

from .authentication import login, logout
from .database import bot_db
from .metrics import UsageTracking
from .summarize import summarize


class WordcabBot(discord.Client):
    """Wordcab Discord Bot."""
    def __init__(
        self,
        *args,
        web_client: ClientSession,
        intents: Optional[discord.Intents] = None,
        testing_guild_id: Optional[int] = None,
    ):
        """Client initialization."""
        if intents is None:
            intents = discord.Intents.default()
        intents.members = True

        super().__init__(intents=intents)
        self.usage_tracking = UsageTracking()
        self.web_client = web_client
        self.testing_guild_id = testing_guild_id
        self.tree = app_commands.CommandTree(self)


    async def on_ready(self):
        await self.wait_until_ready()
        print(f'Logged on as {self.user}!')

    
    async def on_guild_join(self, guild: discord.Guild):
        """On guild join."""
        await bot_db.add_a_guild(discord_guild_id=guild.id, guild_owner_id=guild.owner_id)
        await self.tree.sync(guild=guild)

    
    async def on_guild_remove(self, guild: discord.Guild):
        """On guild remove."""
        await bot_db.remove_a_guild(discord_guild_id=guild.id)
        # await self.tree.sync(guild=guild)


    async def send_summary_as_dm(
        self,
        guild: discord.Guild,
        user: discord.User,
        summary_size: str,
        timeframe: str,
        language: str,
        job_name: str,
        token: str,
        summarized_chat: Optional[List[str]] = None,
    ) -> None:
        """
        Send summary as DM.
        
        Parameters
        ----------
        guild: discord.Guild
            The guild the user is in.
        user: discord.User
            The user to send the summary to.
        summary_size: str
            The summary size used to generate the summary.
        timeframe: str
            The timeframe used to generate the summary.
        language: str
            The language used to generate the summary.
        job_name: str
            The job name.
        token: str
            The Wordcab API token.
        summarized_chat: Optional[List[str]]
            The summarized chat to send if the user requested it.
        """
        while True:
            job = retrieve_job(job_name=job_name, api_key=token)
            status = job.job_status
            if status == "SummaryComplete":
                break
            elif status == "Deleted" or status == "Error":
                await user.send(f"Your job has been [{status}]. Please try again.")
            await asyncio.sleep(3)

        summary_id = job.summary_details["summary_id"]
        await bot_db.store_summary_id(summary_id=summary_id, discord_guild_id=guild.id)
        summary = retrieve_summary(summary_id=summary_id, api_key=token)
        await user.send(f"**Your summary:**")
        for utterance in summary.summary[summary_size]["structured_summary"]:
            await user.send(f"```{utterance.summary}```")

        if summarized_chat is not None:
            await user.send("**Chats used for the summary:**")
            # Send the summarized chat in chunks of 2000 characters
            joined_chat: str = ""
            for chat in summarized_chat:
                if len(joined_chat) + len(chat) > 2000:
                    await user.send(f"```{joined_chat}```")
                    joined_chat = ""
                joined_chat += f"\n{chat}"
            await user.send(f"```{joined_chat}```")

        include_chat = True if summarized_chat is not None else False
        time_started = datetime.strptime(summary.time_started, "%Y-%m-%dT%H:%M:%S.%fZ")
        time_completed = datetime.strptime(summary.time_completed, "%Y-%m-%dT%H:%M:%S.%fZ")
        response_time = (time_completed - time_started).total_seconds()
        self.usage_tracking.log_metrics(
            user=user.name,
            guild_name=guild.name,
            summary_size=summary_size,
            timeframe=timeframe,
            language=language,
            include_chat=include_chat,
            time_started=time_started,
            time_completed=time_completed,
            response_time=response_time,
        )
        
        # Delete job and users data after summary is sent
        await self.delete_job_after_summary(job_name=job_name, token=token)

    
    async def delete_job_after_summary(self, job_name: str, token: str) -> None:
        """Delete job after summary is complete."""
        job = retrieve_job(job_name=job_name, api_key=token)
        if job.job_status == "SummaryComplete":
            delete_job(job_name=job_name, api_key=token)


    async def setup_hook(self) -> None:
        """Setup Hook."""
        await bot_db.init_db_and_tables()

        self.tree.add_command(login)
        self.tree.add_command(logout)
        self.tree.add_command(summarize)
        await self.tree.sync()

        if self.testing_guild_id is not None:
            try:
                testing_guild = discord.Object(self.testing_guild_id)
                testing_guild.owner_id = (await self.fetch_guild(testing_guild.id)).owner_id
                await bot_db.add_a_guild(discord_guild_id=testing_guild.id, guild_owner_id=testing_guild.owner_id)
                self.tree.copy_global_to(guild=testing_guild)
                await self.tree.sync(guild=testing_guild)
            except discord.errors.Forbidden:
                print("Bot is not in the testing guild.")


async def main():
    """Main function."""
    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename=f"{os.getenv('DATABASE_VOLUME')}/discord.log",
        encoding="utf-8",
        maxBytes=32 * 1024 * 1024,  #32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", date_format, style="{")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Start async session
    async with ClientSession() as web_client:
        async with WordcabBot(
            commands.when_mentioned,
            web_client=web_client,
            testing_guild_id=os.getenv("TESTING_GUILD_ID", None),
        ) as client:
            await client.start(os.getenv("DISCORD_TOKEN", ""))


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
