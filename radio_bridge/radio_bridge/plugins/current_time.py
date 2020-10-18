import datetime

from radio_bridge.plugins.base import BaseDTMFPlugin

__all__ = ["CurrentTimePlugin"]

TEXT = """
Current time is {hour_local} {minute_local} local. {hour_utc}, {minute_utc} U T C.
""".strip()


class CurrentTimePlugin(BaseDTMFPlugin):
    """
    Plugin which says current time.
    """

    ID = "current_time"
    NAME = "Current time"
    DESCRIPTION = "Current date and time."
    DTMF_SEQUENCE = "23"

    def run(self):
        now_local = datetime.datetime.now()
        now_utc = datetime.datetime.utcnow()

        text = TEXT.format(
            hour_local=now_local.hour,
            minute_local=now_local.minute,
            hour_utc=now_utc.hour,
            minute_utc=now_utc.minute,
        )
        self.say(text=text)
