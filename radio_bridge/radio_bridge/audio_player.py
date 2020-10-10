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

LOG = structlog.getLogger(__name__)

__all__ = ["AudioPlayer"]


class AudioPlayer(object):
    def play_file(self, file_path: str, delete_after_play=False) -> None:
        _, ext = os.path.splitext(file_path)

        if ext not in [".mp3", ".wav"]:
            raise ValueError("Unsupported file format: %s (%s)" % (ext, file_path))

        LOG.debug("Playing audio file %s" % (file_path))

        if ext == ".mp3":
            self._play_mp3(file_path=file_path)
        elif ext == ".wav":
            self._play_wav(file_path=file_path)

        if delete_after_play:
            LOG.debug("Removing audio file %s" % (file_path))
            os.unlink(file_path)

    def _play_mp3(self, file_path: str) -> None:
        if not shutil.which("mpg123"):
            raise Exception("Unable to find \"mpg123\" binary. Make sure it's installed on the "
                            "system.")

        args = "mpg123 -q %s" % (shlex.quote(file_path))
        p = subprocess.run(args, shell=True, check=True)
        print(p)

    def _play_wav(self, file_path: str) -> None:
        if not shutil.which("aplay"):
            raise Exception("Unable to find \"aplay\" binary. Make sure it's installed on the "
                            "system.")

        args = "aplay -q %s" % (shlex.quote(file_path))
        subprocess.run(args, shell=True, check=True)
