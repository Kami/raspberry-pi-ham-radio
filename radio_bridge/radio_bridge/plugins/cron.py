from typing import List
from typing import Dict
from typing import Any
from typing import Tuple
from typing import Type

import datetime

import structlog

from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from radio_bridge.plugins.base import BaseRegularPlugin
from radio_bridge.configuration import get_config

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
        "timezone": str
    }
}


class CronSayPlugin(BaseRegularPlugin):
    NAME = "Cron Plugin"

    def __init__(self):
        super(CronSayPlugin, self).__init__()

        # Maps job id to text to say
        self._job_id_to_text_map = self._parse_job_specs()

    def run(self, job_id: str) -> None:
        if job_id not in self._job_id_to_text_map:
            raise ValueError("Unknown job: %s" % (job_id))

        context = self._get_text_format_context()
        print(context)
        text_to_say = self._job_id_to_text_map[job_id].format(**context)
        print(text_to_say)
        self.say(text_to_say)

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
            job_trigger_instance = self._get_job_trigger_for_job_spec(job_id, job_trigger, job_kwargs_str)

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

    def _get_job_trigger_for_job_spec(self, job_id: str, job_trigger: str, job_kwargs_str: str) -> BaseTrigger:
        job_kwargs_dict: Dict[str, Any] = {}

        for pair in job_kwargs_str.split(","):
            key, value = pair.split("=")
            job_kwargs_dict[key] = value

        if job_trigger == "interval":
            cls = IntervalTrigger
        elif job_trigger == "cron":
            cls = CronTrigger
        else:
            raise ValueError("Unknown job trigger specified: %s" % (job_trigger))

        trigger_kwargs = {}

        for kwarg_key, kwarg_type in TRIGGER_TYPE_TO_KWARGS_TYPE_MAP[job_trigger].items():
            trigger_kwarg_value = job_kwargs_dict.get(kwarg_key, None)

            if trigger_kwarg_value is not None:
                trigger_kwargs[kwarg_key] = kwarg_type(trigger_kwarg_value)

        cls_instance = cls(**trigger_kwargs)

        LOG.debug("Using trigger kwargs \"%s\" for scheduler trigger %s and job %s: %s" % (
        str(trigger_kwargs), job_trigger, job_id, cls_instance))

        return cls_instance
