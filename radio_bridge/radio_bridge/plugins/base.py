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
from typing import Callable
from typing import Optional

import os
import sys

import structlog
import pluginlib

from radio_bridge.configuration import get_config
from radio_bridge.tts import TextToSpeech
from radio_bridge.audio_player import AudioPlayer

__all__ = ["BaseDTMFPlugin", "BaseRegularPlugin"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../vendor"))

# Add py-morse to PYTHONPATH
sys.path.append(os.path.join(VENDOR_DIR, "py-morse-code/"))

AUDIO_FILES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../audio_files"))

CALLSIGN_AUDIO_PATH = os.path.join(AUDIO_FILES_DIR, "callsign.mp3")

# Maps DTMF sequence to a plugin class instance (singleton)
DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP: Dict[str, Callable] = {}

LOG = structlog.getLogger(__name__)

INITIALIZED = False


class BasePlugin(object):
    NAME: str
    DESCRIPTION: str

    def __init__(self):
        self._callsign = get_config()["tx"]["callsign"]
        self._tx_mode = get_config()["tx"]["mode"]
        self._tts = TextToSpeech(implementation=get_config()["tts"]["implementation"])
        self._audio_player = AudioPlayer()

    def initialize(self, config) -> None:
        """
        Initialize plugin with plugin specific configuration (if any exists).
        """
        pass

    def enable_tx(self):
        """
        Enable transmit functionality of the radio.
        """
        if self._tx_mode == "vox":
            return

        LOG.trace("Enabling TX mode")

    def disable_tx(self):
        """
        Disable transmit functionality of the radio.
        """
        if self._tx_mode == "vox":
            return

        LOG.trace("Disabling TX mode")

    def say(self, text: str):
        """
        Alias for say_text().
        """
        return self.say_text(text=text)

    def say_text(self, text: str):
        """
        Run tts on the provided text and play it via the audio player.
        """
        self.enable_tx()

        try:
            # 1. Play callsign / hello message
            self._say_callsign()

            # 2. Play actual requested text
            LOG.trace('Playing text "%s"' % (text))

            file_path = self._tts.text_to_speech(text=text)
            self._audio_player.play_file(file_path=file_path, delete_after_play=False)
        finally:
            self.disable_tx()

    def say_text_morse(self, text: str):
        """
        Convert the provided text string to a morse code and play it via the audio player.
        """
        from morse import Morse

        m = Morse(words=text)

        self.enable_tx()

        try:
            # TODO: Play callsign in morse
            LOG.trace('Playing text "%s" as morse code (%s)' % (text, m.morse))

            m.transmit()
        finally:
            self.disable_tx()

    def say_morse(self, text: str):
        """
        Play the provided morse code text string via the audio player.
        """
        from morse import Morse

        m = Morse(morse=text)

        self.enable_tx()

        try:
            # TODO: Play callsign in morse
            LOG.trace('Playing morse code "%s"' % (m.morse))

            m.transmit()
        finally:
            self.disable_tx()

    def _say_callsign(self) -> None:
        if self._callsign.endswith(".mp3") or self._callsign.endswith(".wav"):
            # Assume it's a path to a file
            self._audio_player.play_file(file_path=self._callsign)
        else:
            # Synthesize it
            file_path = self._tts.text_to_speech(text=self._callsign)
            self._audio_player.play_file(file_path=file_path, delete_after_play=False)


@pluginlib.Parent("DTMFPlugin")
class BaseDTMFPlugin(BasePlugin):
    """
    Base class for plugins which are invoked by a specific DTMF sequence.
    """

    NAME: str
    DESCRIPTION: str
    DTMF_SEQUENCE: Optional[str] = None

    @pluginlib.abstractmethod
    def run(self):
        pass


@pluginlib.Parent("DTMFWithDataPlugin")
class BaseDTMFWithDataPlugin(BasePlugin):
    """
    Base class for plugins which are invoked by a specific DTMF sequence and take additiona data
    which is passed to the run() method.
    """

    NAME: str
    DESCRIPTION: str
    DTMF_SEQUENCE: Optional[str] = None

    @pluginlib.abstractmethod
    def run(self, sequence: str):
        pass


@pluginlib.Parent("RegularPlugin")
class BaseRegularPlugin(BasePlugin):
    """
    Base class for plugins which are not tied to a specific DTMF sequence (think timer plugins,
    etc.).
    """

    NAME: str
    DESCRIPTION: str
