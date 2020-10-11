from radio_bridge.plugins.base import BasePlugin

"""
Plugin which resets / clears currently accumulated sequence.
"""

__all__ = ["ClearSequencePlugin"]


class ClearSequencePlugin(BasePlugin):
    NAME = "Clear sequence"
    DTMF_SEQUENCE = "95"

    def run(self):
        pass
