from radio_bridge.plugins.base import BaseDTMFPlugin

"""
Plugin which resets / clears currently accumulated sequence.
"""

__all__ = ["ClearSequencePlugin"]


class ClearSequencePlugin(BaseDTMFPlugin):
    NAME = "Clear sequence"
    DESCRIPTION = "Clear currently accumulated DTMF sequence."
    DTMF_SEQUENCE = "95"

    def run(self):
        pass
