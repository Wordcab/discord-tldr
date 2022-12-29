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

import csv
import glob
import os
from datetime import datetime
from typing import Optional


class UsageTracking:
    """Usage tracking class."""
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or os.getenv("DATABASE_VOLUME")
        self.metrics_folder = f"{self.data_path}/metrics"
        
        if not os.path.exists(self.metrics_folder):
            os.makedirs(self.metrics_folder)

        self._update_metrics_file_list()

    def log_metrics(
        self,
        user: str,
        guild_name: str,
        summary_size: str,
        timeframe: str,
        language: str,
        include_chat: bool,
        time_started: datetime,
        time_completed: datetime,
        response_time: str,
    ):
        """
        Log metrics.
        
        Parameters
        ----------
        user : str
            User name.
        guild_name : str
            Guild name.
        summary_size : str
            Summary size between short, medium, and long.
        timeframe : str
            The timeframe used to generate the summary.
        language : str
            The language used to generate the summary.
        include_chat : bool
            Whether the chat is included along with the summary.
        time_started : datetime
            The time the summary generation started.
        time_completed : datetime
            The time the summary generation completed.
        response_time : str
            The time it took to generate the summary.
        """
        if not self._check_if_last_file_exists():
            self._create_new_metrics_file()
        last_csv = self.metrics_files[-1]
        with open(last_csv, "a") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    user,
                    guild_name,
                    summary_size,
                    timeframe,
                    language,
                    include_chat,
                    time_started,
                    time_completed,
                    response_time,
                ]
            )
    
    def _check_if_last_file_exists(self):
        if not self.metrics_files:
            return False
        else:
            return True
        
    def _create_new_metrics_file(self):
        """Create a new metrics file."""
        with open(
            f"{self.metrics_folder}/{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.csv",
            "w",
        ) as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "user",
                    "guild_name",
                    "summary_size",
                    "timeframe",
                    "language",
                    "include_chat",
                    "time_started",
                    "time_completed",
                    "response_time",
                ]
            )
        self._update_metrics_file_list()
        
    def _update_metrics_file_list(self):
        """Update the list of metrics files."""
        self.metrics_files = glob.glob(f"{self.metrics_folder}/*.csv")
