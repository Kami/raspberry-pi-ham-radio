from typing import Dict
from typing import Callable
from typing import Optional

import os

import structlog
import pluginlib

from radio_bridge.tts import TextToSpeech
from radio_bridge.audio_player import AudioPlayer

__all__ = ["BasePlugin"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FILES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../audio_files"))

CALLSIGN_AUDIO_PATH = os.path.join(AUDIO_FILES_DIR, "callsign.mp3")

# Maps DTMF sequence to a plugin class instance (singleton)
DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP: Dict[str, Callable] = {}

LOG = structlog.getLogger(__name__)

INITIALIZED = False


@pluginlib.Parent("DTMFPlugin")
class BasePlugin(object):
    NAME: str
    DTMF_SEQUENCE: Optional[str] = None

    def __init__(self):
        self._tts = TextToSpeech()
        self._audio_player = AudioPlayer()

    def initialize(self, config) -> None:
        """
        Initialize plugin with plugin specific configuration (if any exists).
        """
        pass

    @pluginlib.abstractmethod
    def run(self):
        pass

    def enable_tx(self):
        """
        Enable transmit functionality of the readio.
        """
        pass

    def disable_tx(self):
        """
        Disable transmit functionality of the readio.
        """
        pass

    def say(self, text: str):
        """
        Run tts on the provided text and play it via the audi player.
        """
        # 1. Play callsign / hello message
        self._audio_player.play_file(file_path=CALLSIGN_AUDIO_PATH)

        # 2. Play actual requested text
        # TODO: Add support for caching playbacks for a while.
        # Use hash of text for unique id
        file_path = self._tts.text_to_speech(text=text)
        self._audio_player.play_file(file_path=file_path, delete_after_play=False)
