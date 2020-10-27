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

import mock

from radio_bridge.audio_player import AudioPlayer
from radio_bridge.audio_player import get_audio_file_duration

from tests.unit.base import BaseTestCase

__all__ = ["AudioPlayerTestCase"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MP3_FILE_PATH = os.path.join(BASE_DIR, "../fixtures/audio/plugin_current_time.mp3")
WAV_FILE_PATH = os.path.join(BASE_DIR, "../fixtures/audio/plugin_current_time.wav")


def Any(cls):
    class Any(cls):
        def __eq__(self, other):
            return True

    return Any()


class AudioPlayerTestCase(BaseTestCase):
    """
    It's relatively hard to test this functionality end to end so we use mocking.
    """

    @mock.patch("shutil.which", mock.Mock(return_value="/bin/mpg123"))
    @mock.patch("subprocess.run")
    def test_play_mp3(self, mock_run):
        audio_player = AudioPlayer()
        audio_player.play_file(file_path=MP3_FILE_PATH)

        mock_run.assert_called_with(
            "mpg123 -q %s" % (MP3_FILE_PATH), shell=True, check=True, preexec_fn=Any(object)
        )

    @mock.patch("shutil.which", mock.Mock(return_value="/bin/aplay"))
    @mock.patch("subprocess.run")
    def test_play_wav(self, mock_run):
        audio_player = AudioPlayer()
        audio_player.play_file(file_path=WAV_FILE_PATH)

        mock_run.assert_called_with(
            "aplay -q %s" % (WAV_FILE_PATH), shell=True, check=True, preexec_fn=Any(object)
        )

    def test_get_audio_file_duration(self):
        duration = get_audio_file_duration(MP3_FILE_PATH)
        self.assertEqual(duration, 6.048)

        duration = get_audio_file_duration(WAV_FILE_PATH)
        self.assertEqual(duration, 6.048)
