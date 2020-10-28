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
import shutil
import tempfile

from radio_bridge.tts import TextToSpeech
from radio_bridge.audio_player import get_audio_file_duration
from radio_bridge.configuration import set_config_option

from tests.unit.base import BaseTestCase

__all__ = ["TTSTestCase"]


class TTSTestCase(BaseTestCase):
    """
    NOTE: For now we only test that a file has been created on disk.

    Sadly we can't really assert on the content since all the audio -> text aka transcribe engines
    which work offline need a custom trained mode to be somewhat accurate.
    """

    def setUp(self):
        super(TTSTestCase, self).setUp()

        self._temp_dir = tempfile.mkdtemp()

        set_config_option("tts", "enable_cache", "True")
        set_config_option("tts", "cache_directory", self._temp_dir)

    def tearDown(self):
        super(TTSTestCase, self).tearDown()

        assert self._temp_dir.startswith("/tmp")
        shutil.rmtree(self._temp_dir)

    def test_text_to_speech_gtts(self):
        tts = TextToSpeech(implementation="gtts")

        text = "Hello World. Test."
        output_file_path = tts._tts._get_cache_file_path(text=text, use_cache=True)

        self.assertFalse(os.path.isfile(output_file_path))

        tts.text_to_speech(text=text)
        self.assertTrue(os.path.isfile(output_file_path))

        duration = get_audio_file_duration(file_path=output_file_path)
        self.assertTrue(duration >= 1.5)

    def test_text_to_speech_speak(self):
        tts = TextToSpeech(implementation="espeak")

        text = "Hello World. Test."
        output_file_path = tts._tts._get_cache_file_path(text=text, use_cache=True)

        self.assertFalse(os.path.isfile(output_file_path))

        tts.text_to_speech(text=text)
        self.assertTrue(os.path.isfile(output_file_path))

        duration = get_audio_file_duration(file_path=output_file_path)
        self.assertTrue(duration >= 1.5)