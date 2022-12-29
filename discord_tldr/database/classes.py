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

from typing import Optional

from sqlmodel import Field, SQLModel


class Guilds(SQLModel, table=True):
    """Guilds table."""
    id: Optional[int] = Field(default=None, primary_key=True)
    logged_in: bool = Field(default=False)
    discord_guild_id: int = Field(unique=True, index=True)
    guild_owner_id: int

class Credentials(SQLModel, table=True):
    """Credentials table."""
    id: int = Field(primary_key=True)
    email: str
    token: str
    guild_id: int = Field(foreign_key="guilds.id")

class Members(SQLModel, table=True):
    """Members table."""
    id: int = Field(primary_key=True)
    guild_id: int = Field(foreign_key="guilds.id")
    member_id: int
    authorized: bool = Field(default=False)

class Summaries(SQLModel, table=True):
    """Summaries table."""
    id: int = Field(primary_key=True)
    guild_id: int = Field(foreign_key="guilds.id")
    summary_id: str