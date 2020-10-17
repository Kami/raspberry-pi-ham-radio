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
        p = subprocess.run(args, shell=True, check=True)
        print(p)

    def _play_wav(self, file_path: str) -> None:
        if not shutil.which("aplay"):
            raise Exception(
                'Unable to find "aplay" binary. Make sure it\'s installed on the ' "system."
            )

        wav = WAVE(file_path)
        duration = wav.info.length

        LOG.trace('Playing audio file "%s"' % (file_path), duration=duration)

        args = "aplay -q %s" % (shlex.quote(file_path))
        subprocess.run(args, shell=True, check=True)


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
