from radio_bridge.plugins.base import BaseDTMFWithDataPlugin

"""
Plugin which resets / clears currently accumulated sequence.
"""

__all__ = ["ClearSequencePlugin"]


class ClearSequencePlugin(BaseDTMFWithDataPlugin):
    """
    Special plugin which can be triggered any time and causes currently accumulated DTMF sequence
    to be cleared (this comes handy in case of a typo or similar).
    """
    NAME = "Clear sequence"
    DESCRIPTION = "Clear currently accumulated DTMF sequence."
    DTMF_SEQUENCE = "*D*"

    def run(self, sequence: str):
        pass
