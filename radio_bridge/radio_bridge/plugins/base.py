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
from typing import Tuple

import os
import sys
import fnmatch
import multiprocessing

import structlog
import pluginlib

from radio_bridge.configuration import get_config
from radio_bridge.tts import TextToSpeech
from radio_bridge.audio_player import AudioPlayer
from radio_bridge.otp import validate_otp

__all__ = [
    "BaseDTMFPlugin",
    "BaseDTMFWithDataPlugin",
    "BaseNonDTMFPlugin",
    "BaseAdminDTMFPlugin",
    "BaseAdminDTMFWithDataPlugin",
]

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
    REQUIRES_INTERNET_CONNECTION: bool

    def __init__(self):
        self._callsign = get_config()["tx"]["callsign"]
        self._tx_mode = get_config()["tx"]["mode"]
        self._gpio_pin = get_config().get("tx", "gpio_pin", fallback=None)
        self._audio_player = AudioPlayer()

        self._config = {}

    @property
    def _tts(self):
        # NOTE: We instantiate this object lazily on demand so any changes to the config state made
        # during the program life cycle are reflected here.
        print(get_config()["tts"]["implementation"])
        return TextToSpeech(implementation=get_config()["tts"]["implementation"])

    def initialize(self, config: dict) -> None:
        """
        Initialize plugin with plugin specific configuration and validate it (if any exists).
        """
        self._config = config

    def enable_tx(self):
        """
        Enable transmit functionality of the radio.
        """
        if self._tx_mode == "vox":
            return

        import RPi.GPIO as GPIO

        LOG.trace("Enabling TX mode", gpio_pin=self._gpio_pin)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._gpio_pin, GPIO.OUT)

        GPIO.output(self._gpio_pin, GPIO.HIGH)

    def disable_tx(self):
        """
        Disable transmit functionality of the radio.
        """
        if self._tx_mode == "vox":
            return

        import RPi.GPIO as GPIO

        LOG.trace("Disabling TX mode", gpio_pin=self._gpio_pin)

        GPIO.output(self._gpio_pin, GPIO.LOW)

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

    def run_in_subprocess(self, queue: multiprocessing.Queue):
        """
        Method which is called when using process executor.

        It takes in queue argument which is used to pass the result back to the main process.
        """
        result = self.run()
        queue.put(result)
        return result

    def matches_dtmf_sequence(self, sequence: str) -> Tuple[bool, Tuple, Dict]:
        """
        Return true if this plugin matches the provided sequence and return any additional args and
        kwargs which should be passed to the plugin run method.
        """
        return (sequence == self.DTMF_SEQUENCE, (), {})


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

    def run_in_subprocess(self, queue, sequence: str):
        """
        Method which is called when using process executor.

        It takes in queue argument which is used to pass the result back to the main process.
        """
        result = self.run(sequence=sequence)
        queue.put(result)
        return result

    def matches_dtmf_sequence(self, sequence: str) -> Tuple[bool, Tuple, Dict]:
        """
        Return true if this plugin matches the provided sequence and return any additional args and
        kwargs which should be passed to the plugin run method.
        """
        plugin_sequence = self.DTMF_SEQUENCE

        if fnmatch.fnmatch(sequence, plugin_sequence):
            args = ()
            kwargs = {}

            if "?" in plugin_sequence:
                data_sequence = sequence.replace(plugin_sequence.split("?", 1)[0], "")
                kwargs["sequence"] = data_sequence
                return (True, args, kwargs)
            elif "*" in plugin_sequence:
                kwargs["sequence"] = plugin_sequence
                return (True, args, kwargs)

        return (False, (), {})


@pluginlib.Parent("AdminDTMFPlugin")
class BaseAdminDTMFPlugin(BaseDTMFPlugin):
    """
    Base class for all the admin plugins.

    Admin plugins are special because in addition to the plugin code, they take 4 characters long
    OTP sequence
    """

    NAME: str
    DESCRIPTION: str
    DTMF_SEQUENCE: Optional[str] = None

    @pluginlib.abstractmethod
    def run(self):
        pass

    def matches_dtmf_sequence(self, sequence: str) -> Tuple[bool, Tuple, Dict]:
        """
        Return true if this plugin matches the provided sequence and return any additional args and
        kwargs which should be passed to the plugin run method.
        """
        # OTP is 4 digits long, hence the ????
        plugin_sequence = self.DTMF_SEQUENCE + "????"

        if fnmatch.fnmatch(sequence, plugin_sequence):
            otp_sequence = sequence.replace(plugin_sequence.split("?", 1)[0], "")

            if validate_otp(otp_sequence):
                return True, (), {}

        return (False, (), {})


@pluginlib.Parent("AdminDTMFWithDataPlugin")
class BaseAdminDTMFWithDataPlugin(BaseDTMFPlugin):
    """
    Base class for all the admin which take data plugins.

    Admin plugins are special because in addition to the plugin code, they take 4 characters long
    OTP sequence
    """

    NAME: str
    DESCRIPTION: str
    DTMF_SEQUENCE: Optional[str] = None

    @pluginlib.abstractmethod
    def run(self, sequence: str):
        pass

    def run_in_subprocess(self, queue, sequence: str):
        """
        Method which is called when using process executor.

        It takes in queue argument which is used to pass the result back to the main process.
        """
        result = self.run(sequence=sequence)
        queue.put(result)
        return result

    def matches_dtmf_sequence(self, sequence: str) -> Tuple[bool, Tuple, Dict]:
        """
        Return true if this plugin matches the provided sequence and return any additional args and
        kwargs which should be passed to the plugin run method.
        """
        # OTP is 4 digits long, hence the ????
        # We also support admin plugin taking any additional data which comes after the OTP
        plugin_sequence = self.DTMF_SEQUENCE

        split = plugin_sequence.split("?")

        plugin_sequence_static = split[0]
        plugin_sequence_data = "".join(["?" for char in split[1:]])

        plugin_sequence = plugin_sequence_static + "????" + plugin_sequence_data
        plugin_sequence_data_len = len(plugin_sequence_data)

        if fnmatch.fnmatch(sequence, plugin_sequence):
            partial_sequence = sequence.replace(plugin_sequence.split("?", 1)[0], "")

            otp_sequence = partial_sequence[:-plugin_sequence_data_len]
            data_sequence = partial_sequence[4:]
            kwargs = {"sequence": data_sequence}

            if validate_otp(otp_sequence):
                return True, (), kwargs

        return (False, (), {})


@pluginlib.Parent("NonDTMFPlugin")
class BaseNonDTMFPlugin(BasePlugin):
    """
    Base class for plugins which are not tied to a specific DTMF sequence (think timer plugins,
    etc.).
    """

    NAME: str
    DESCRIPTION: str
