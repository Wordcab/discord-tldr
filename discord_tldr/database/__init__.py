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

import os
from dotenv import load_dotenv

from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import create_async_engine

from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .classes import Credentials, Guilds, Summaries


load_dotenv()
DATABASE_VOLUME = os.getenv("DATABASE_VOLUME")


class BotDB():
    """Bot Database."""
    def __init__(self):
        """Initialization."""
        self.sqlite_file_name = f"{DATABASE_VOLUME}/bot-database.db"
        self.sqlite_url = f"sqlite+aiosqlite:///{self.sqlite_file_name}"

        self.engine = create_async_engine(self.sqlite_url, echo=True)


    async def init_db_and_tables(self):
        """Initialize the database and the tables."""
        async with self.engine.begin() as session:
            await session.run_sync(SQLModel.metadata.create_all)


    async def add_a_guild(self, discord_guild_id: int, guild_owner_id: int):
        """Add a guild."""
        async with AsyncSession(self.engine) as session:
            guild = await session.exec(select(Guilds).where(Guilds.discord_guild_id == discord_guild_id))
            try:
                guild = guild.one()
                print("Guild already exists.")
            except NoResultFound:
                guild = Guilds(discord_guild_id=discord_guild_id, guild_owner_id=guild_owner_id)
                session.add(guild)
                await session.commit()
                await session.refresh(guild)


    async def authenticate_a_guild(self, guild_id: int, email: str, token: str):
        """Authenticate a guild."""
        async with AsyncSession(self.engine) as session:
            guild = await session.exec(select(Guilds).where(Guilds.id == guild_id))
            guild = guild.one()
            guild.logged_in = True
            credentials = Credentials(email=email, token=token, guild_id=guild.id)
            session.add(credentials)
            await session.commit()
            await session.refresh(guild)
            await session.refresh(credentials)


    async def get_a_guild_id(self, discord_guild_id: int):
        """Get a guild id."""
        async with AsyncSession(self.engine) as session:
            guild = await session.exec(select(Guilds).where(Guilds.discord_guild_id == discord_guild_id))
            guild = guild.one()
            return guild.id

    
    async def unauthenticate_a_guild(self, discord_guild_id: int):
        """Unauthenticate a guild."""
        async with AsyncSession(self.engine) as session:
            guild = await session.exec(select(Guilds).where(Guilds.discord_guild_id == discord_guild_id))
            guild = guild.one()
            guild.logged_in = False
            credentials = await session.exec(select(Credentials).where(Credentials.guild_id == guild.id))
            session.delete(credentials)
            await session.commit()
            await session.refresh(guild)


    async def is_guild_authenticated(self, discord_guild_id: int):
        """Check if a guild is authenticated."""
        async with AsyncSession(self.engine) as session:
            guild = await session.exec(select(Guilds).where(Guilds.discord_guild_id == discord_guild_id))
            guild = guild.first()
            return guild.logged_in


    async def get_guild_token(self, discord_guild_id: int):
        """Get a guild token."""
        async with AsyncSession(self.engine) as session:
            guild = await session.exec(select(Guilds).where(Guilds.discord_guild_id == discord_guild_id))
            guild = guild.one()
            credentials = await session.get(Credentials, guild.id)
            return credentials.token


    async def remove_a_guild(self, discord_guild_id: int):
        """Remove a guild."""
        async with AsyncSession(self.engine) as session:
            guild = await session.exec(select(Guilds).where(Guilds.discord_guild_id == discord_guild_id))
            guild = guild.one()
            session.delete(guild)
            await session.commit()

    
    async def store_summary_id(self, discord_guild_id: str, summary_id: str):
        """Store a summary id."""
        async with AsyncSession(self.engine) as session:
            guild = await session.exec(select(Guilds).where(Guilds.discord_guild_id == discord_guild_id))
            guild = guild.one()
            summary = Summaries(summary_id=summary_id, guild_id=guild.id)
            session.add(summary)
            await session.commit()
            await session.refresh(summary)


bot_db = BotDB()
