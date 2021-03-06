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

"""
Audio player class which is responsibel for playing recorded files.

This class assumes the system has been correctly configured that the USB sound card line out is the
default line out.
"""

import os
import os.path
import shutil
import shlex
import subprocess

import structlog

from mutagen.mp3 import MP3
from mutagen.wave import WAVE

from radio_bridge.utils.subprocess import on_parent_exit

LOG = structlog.getLogger(__name__)

__all__ = ["AudioPlayer", "get_audio_file_duration"]


class AudioPlayer(object):
    def play_file(self, file_path: str, delete_after_play=False) -> None:
        _, ext = os.path.splitext(file_path)

        if ext not in [".mp3", ".wav"]:
            raise ValueError("Unsupported file format: %s (%s)" % (ext, file_path))

        if ext == ".mp3":
            self._play_mp3(file_path=file_path)
        elif ext == ".wav":
            self._play_wav(file_path=file_path)

        if delete_after_play:
            LOG.debug("Removing audio file %s" % (file_path))
            os.unlink(file_path)

    def _play_mp3(self, file_path: str) -> None:
        if not shutil.which("mpg123"):
            raise Exception(
                'Unable to find "mpg123" binary. Make sure it\'s installed on the ' "system."
            )

        mp3 = MP3(file_path)
        duration = mp3.info.length

        LOG.trace('Playing audio file "%s"' % (file_path), duration=duration)

        args = "mpg123 -q %s" % (shlex.quote(file_path))
        # NOTE: We set preexec_fn since we want child process to also be killed if the parent is
        # killed
        subprocess.run(args, shell=True, check=True, preexec_fn=on_parent_exit("SIGTERM"))

    def _play_wav(self, file_path: str) -> None:
        if not shutil.which("aplay"):
            raise Exception(
                'Unable to find "aplay" binary. Make sure it\'s installed on the ' "system."
            )

        wav = WAVE(file_path)
        duration = wav.info.length

        LOG.trace('Playing audio file "%s"' % (file_path), duration=duration)

        args = "aplay -q %s" % (shlex.quote(file_path))
        # NOTE: We set preexec_fn since we want child process to also be killed if the parent is
        # killed
        subprocess.run(args, shell=True, check=True, preexec_fn=on_parent_exit("SIGTERM"))


def get_audio_file_duration(file_path: str) -> float:
    _, ext = os.path.splitext(file_path)

    if ext not in [".mp3", ".wav"]:
        raise ValueError("Unsupported file format: %s (%s)" % (ext, file_path))

    if ext == ".mp3":
        mp3 = MP3(file_path)
        duration = mp3.info.length
    elif ext == ".wav":
        wav = WAVE(file_path)
        duration = wav.info.length

    return duration
