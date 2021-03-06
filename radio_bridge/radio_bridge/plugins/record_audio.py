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

import os
import datetime

import wave
import pyaudio
import structlog

from radio_bridge.plugins.base import BaseNonDTMFPlugin
from radio_bridge.configuration import get_plugin_config_option


LOG = structlog.getLogger(__name__)

__all__ = ["RecordAudioPlugin"]


class RecordAudioPlugin(BaseNonDTMFPlugin):
    ID = "record_audio"
    NAME = "Record Audio"
    DESCRIPTION = "Record audio and write it to a file on disk."
    REQUIRES_INTERNET_CONNECTION = False
    DEFAULT_LANGUAGE = "en_US"
    SUPPORTED_LANGUAGES = ["en_US"]

    _skipload_ = get_plugin_config_option(ID, "enable", "bool", fallback=True) is False

    def initialize(self, config: dict) -> None:
        super(RecordAudioPlugin, self).initialize(config=config)

        if not os.path.isdir(self._config["data_dir"]):
            os.makedirs(self._config["data_dir"])

        self._record_duration = float(self._config["record_duration"])
        self._channels = int(self._config["channels"])
        self._input_device_index = int(self._config["input_device_index"])
        self._rate = int(self._config["sample_rate"])

        self._audio = pyaudio.PyAudio()

    def run(self):
        # TODO: Refactor plugin to use a single pyaudio instance for this plugin + main loop and
        # share data via queue.
        # This is more efficient and only requires us to run a single record audio function.
        # TODO: Throw if executor used is not process
        chunk_size = 2 ** 12

        stream = self._audio.open(
            format=pyaudio.paInt16,
            input_device_index=self._input_device_index,
            channels=self._channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=chunk_size,
        )

        file_name = datetime.datetime.utcnow().strftime("%Y-%M-%d-%H:%M:%S") + ".wav"
        file_path = os.path.join(self._config["data_dir"], file_name)

        LOG.info(
            "Recording audio with duration of %s seconds to %s" % (self._record_duration, file_path)
        )

        frames_buffer = []
        # TODO: Add support for removing silence
        for i in range(0, int(self._rate / chunk_size * self._record_duration)):
            data = stream.read(chunk_size, exception_on_overflow=False)
            frames_buffer.append(data)

        LOG.info("Audio recording stored to %s" % (file_path))
        self._write_frame_buffer_to_file(frames_buffer=frames_buffer, file_path=file_path)

    def _write_frame_buffer_to_file(self, frames_buffer: list, file_path: str) -> None:
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(self._channels)
            wf.setsampwidth(self._audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self._rate)
            wf.writeframes(b"".join(frames_buffer))
