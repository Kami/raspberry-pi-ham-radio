import os
import tempfile
import hashlib

import structlog
from gtts import gTTS

LOG = structlog.getLogger(__name__)

CACHED_AUDO_FILES_PATH = "/tmp/gtts-audio-cache"


class TextToSpeech(object):
    """
    Text To Speech implementation based on online Google gTTS.
    """

    def __init__(self):
        os.makedirs(CACHED_AUDO_FILES_PATH, exist_ok=True)

    def text_to_speech(self, text: str, slow: bool = False, use_cache: bool = True) -> str:
        """
        Perform tts on the provided text string and write result to a file.
        """
        # TODO: Add cron job which auto purges old recording cached files
        file_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        file_name = "%s.mp3" % (file_hash)
        file_path = os.path.join(CACHED_AUDO_FILES_PATH, file_name)

        if use_cache:
            if os.path.isfile(file_path):
                LOG.info("Using cache file: %s" % (file_path))
                return file_path

        audio_file = gTTS(text=text,
                          lang="en-US",
                          slow=slow,
                          lang_check=False)

        audio_file.save(file_path)

        return file_path
