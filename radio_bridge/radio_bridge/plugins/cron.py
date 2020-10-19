# -*- coding: utf-8 -*-
# Copyright 2020 Tomaz Muraus
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

from typing import Dict
from typing import Any
from typing import Tuple
from typing import Type

import os
import re
import datetime

import structlog

from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from radio_bridge.plugins.base import BaseRegularPlugin
from radio_bridge.configuration import get_config
from radio_bridge.audio_player import get_audio_file_duration

"""
Plugin which allows schedueling of say task to run at specific intervals.
"""

LOG = structlog.getLogger(__name__)

JOB_SPEC_DELIMITER = ";"

TRIGGER_TYPE_TO_KWARGS_TYPE_MAP = {
    "interval": {
        "weeks": str,
        "days": int,
        "hours": int,
        "minutes": int,
        "seconds": int,
        "start_date": str,
        "end_date": str,
        "timezone": str,
    }
}

# Maximum playback duration in seconds for the synthesised text or played audio files
# TODO: Define in config
MAXIMUM_PLAYBACK_DURATION = 30

# We assume saying / playing a single world takes 1 second on average (less for short words,
# longer for longer ones. this also doesn't include punctuations, etc)
AVERAGE_AUDIO_DURATION_PER_WORD = 1

# Minimum interval for trigger in seconds. Jobs can't run more often than this specified einterval.
MINIMUM_TRIGGER_INTERVAL = 120

DEV_MODE = get_config()["main"].getboolean("dev_mode")


class CronSayItemConfig(object):
    # Job id
    job_id: str

    # Job trigger instance based on the original parsed job_kwargs
    trigger_instance: BaseTrigger

    # Item type (text, audio)
    type: str

    # Item value - text to say for text jobs, path to audio file to play for audio jobs
    value: str

    def __init__(self, job_id: str, trigger_instance: BaseTrigger, type: str, value: str):
        self.job_id = job_id
        self.trigger_instance = trigger_instance
        self.type = type
        self.value = value

        if self.type == "file" and not os.path.isfile(self.value):
            raise ValueError("File %s doesn't exist" % (self.value))

        # Lazily populated on first .duration property access
        self._duration = None

    @property
    def duration(self):
        if not self._duration:
            if self.type == "text":
                self._duration = CronSayPlugin.calculate_duration_for_text(text=self.value)
            elif self.type == "file":
                self._duration = get_audio_file_duration(file_path=self.value)

        return self._duration

    # TODO: Add __repr__
    def __repr__(self):
        value = self.value

        if self.type == "file":
            value = os.path.basename(self.value)

        return (
            "<CronSayItemConfig job_id=%s,trigger_instance=%s,type=%s,value=%s,play_duration=%ss>"
            % (self.job_id, self.trigger_instance, self.type, value, self.duration)
        )


class CronSayPlugin(BaseRegularPlugin):
    NAME = "Cron Plugin"
    DESCRIPTION = "Say text on play an audio file on defined time interval(s)."
    REQUIRES_INTERNET_CONNECTION = False

    def __init__(self):
        super(CronSayPlugin, self).__init__()

        plugin_config = get_config()["plugin:cron"]
        self._job_id_to_config_map = self._parse_and_validate_config(plugin_config)

    def run(self, job_id: str) -> None:
        if job_id not in self._job_id_to_config_map:
            raise ValueError("Unknown job: %s" % (job_id))

        job_config = self._job_id_to_config_map[job_id]
        value = self._job_id_to_config_map[job_id].value

        if job_config.type == "text":
            context = self._get_text_format_context()
            text_to_say = value.format(**context)
            self.say(text_to_say)
        elif job_config.type == "text_to_morse":
            self.say_text_morse(text=value)
        elif job_config.type == "morse":
            self.say_morse(text=value)
        elif job_config.type == "file":
            self._audio_player.play_file(file_path=job_config.value, delete_after_play=False)

    def _parse_and_validate_config(self, config) -> Dict[str, CronSayItemConfig]:
        plugin_config = get_config()["plugin:cron"]

        result = {}
        for job_id, job_specs in plugin_config.items():
            split = job_specs.split(JOB_SPEC_DELIMITER)

            if len(split) != 4:
                raise ValueError('Plugin job specification "%s" is invalid' % (job_specs))

            job_trigger = split[0]
            job_kwargs_str = split[1]
            job_type = split[2]
            job_value = split[3]

            if job_type not in ["text", "text_to_morse", "morse", "file"]:
                raise ValueError('Unknown job type "%s" for job %s' % (job_type, job_id))

            trigger_instance = self._get_job_trigger_for_job_spec(
                job_id, job_trigger, job_kwargs_str
            )
            item = CronSayItemConfig(
                job_id=job_id, trigger_instance=trigger_instance, type=job_type, value=job_value
            )

            trigger_interval_seconds = self._get_interval_in_seconds(item.trigger_instance)

            if not DEV_MODE and trigger_interval_seconds < MINIMUM_TRIGGER_INTERVAL:
                raise ValueError(
                    "Requested interval for job %s is %s seconds, but minimum "
                    "allowed value is %s seconds"
                    % (job_id, trigger_interval_seconds, MINIMUM_TRIGGER_INTERVAL)
                )

            if not DEV_MODE and item.duration > MAXIMUM_PLAYBACK_DURATION:
                raise ValueError(
                    "Calculated audio duration for job %s is longer than maximum "
                    "allowed (%s seconds > %s seconds)"
                    % (job_id, item.duration, MAXIMUM_PLAYBACK_DURATION)
                )

            result[job_id] = item

        return result

    def _get_interval_in_seconds(self, trigger_instance: BaseTrigger) -> int:
        """
        Return interval in seconds for the provided trigger instance.
        """
        if isinstance(trigger_instance, IntervalTrigger):
            weeks = getattr(trigger_instance.interval, "weeks", 0)
            days = getattr(trigger_instance.interval, "days", 0)
            hours = getattr(trigger_instance.interval, "hours", 0)
            seconds = getattr(trigger_instance.interval, "seconds", 0)
        elif isinstance(trigger_instance, CronTrigger):
            # TODO
            weeks, days, hours, seconds = 0, 0, 0, 0

        return (weeks * 7 * 24 * 60 * 60) + (days * 24 * 60 * 60) + (hours * 60 * 60) + seconds

    @classmethod
    def calculate_duration_for_text(cls, text: str, slow: bool = False) -> int:
        """
        Calculate approximate duration of audio generated by gTTS for the provided text string.
        """
        words = re.split(r"\s+", text)

        duration = len(words) * AVERAGE_AUDIO_DURATION_PER_WORD

        if slow:
            duration *= 1.3

        return duration

    def _get_text_format_context(self) -> Dict[str, str]:
        """
        Return a string format context with which each cron job test is rendered with.

        This allows user to reference various dynamic values in this text such as current time,
        date, etc.
        """
        # TODO: Also add WX data and other useful info to the context.
        context = {}
        context["time_utc"] = datetime.datetime.utcnow().strftime("%H:%M:%S")
        context["time_local"] = datetime.datetime.now().strftime("%H:%M:%S")

        return context

    def get_scheduler_jobs(self) -> Tuple[str, Type[BaseTrigger]]:
        """
        Return a list of jobs to add to the scheduler based on the specifications defined in the
        config.
        """
        # TODO: Specify minimum job run interval (e.g. every 5 minutes) to avoid issues and spam,
        # etc.
        jobs = []

        plugin_config = get_config()["plugin:cron"]

        for job_id, job_specs in plugin_config.items():
            split = job_specs.split(JOB_SPEC_DELIMITER)
            job_trigger = split[0]
            job_kwargs_str = split[1]
            job_trigger_instance = self._get_job_trigger_for_job_spec(
                job_id, job_trigger, job_kwargs_str
            )

            job = (job_id, job_trigger_instance)
            jobs.append(job)

        return jobs

    def _parse_job_specs(self) -> Dict[str, str]:
        plugin_config = get_config()["plugin:cron"]

        result = {}
        for job_id, job_specs in plugin_config.items():
            # -1 last item is always the text to say
            result[job_id] = job_specs.split(JOB_SPEC_DELIMITER)[-1]

        return result

    def _get_job_trigger_for_job_spec(
        self, job_id: str, job_trigger: str, job_kwargs_str: str
    ) -> BaseTrigger:
        """
        Return BaseTrigger instance for the provided CronSay job specification.
        """
        if job_trigger == "interval":
            job_kwargs_dict: Dict[str, Any] = {}

            for pair in job_kwargs_str.split(","):
                key, value = pair.split("=")
                job_kwargs_dict[key] = value

            cls = IntervalTrigger

            trigger_kwargs = {}

            for kwarg_key, kwarg_type in TRIGGER_TYPE_TO_KWARGS_TYPE_MAP[job_trigger].items():
                trigger_kwarg_value = job_kwargs_dict.get(kwarg_key, None)

                if trigger_kwarg_value is not None:
                    trigger_kwargs[kwarg_key] = kwarg_type(trigger_kwarg_value)

            cls_instance = cls(**trigger_kwargs)
        elif job_trigger == "cron":
            cls = CronTrigger
            cls_instance = cls.from_crontab(job_kwargs_str)
        else:
            raise ValueError("Unknown job trigger specified: %s" % (job_trigger))

        LOG.debug(
            'Using trigger kwargs "%s" for scheduler trigger %s and job %s: %s'
            % (str(job_kwargs_str), job_trigger, job_id, cls_instance)
        )

        return cls_instance
