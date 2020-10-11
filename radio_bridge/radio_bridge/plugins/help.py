from radio_bridge.plugins.base import BasePlugin
from radio_bridge.plugins import get_plugins_with_dtmf_sequence

"""
Plugin which says all the available commands.
"""

class HelpPlugin(BasePlugin):
    NAME = "Help Plugin"
    DESCRIPTION = "List available commands."
    DTMF_SEQUENCE = "12"

    def run(self):
        plugins = get_plugins_with_dtmf_sequence()

        text_to_say = "Available commands:"

        for index, plugin_class in enumerate(plugins.values()):
            sequence_text = ""
            for char in plugin_class.DTMF_SEQUENCE:
                sequence_text += char + " "

            text_to_say += "\n%s. %s. Sequence %s. %s" % (index + 1, plugin_class.NAME, sequence_text, plugin_class.DESCRIPTION)

        self.say(text_to_say)