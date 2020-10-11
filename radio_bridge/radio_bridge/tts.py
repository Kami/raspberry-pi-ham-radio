import os
import tempfile
import hashlib

import structlog
from gtts import gTTS

from radio_bridge.configuration import get_config

LOG = structlog.getLogger(__name__)

CACHE_GENERATED_AUDIO_FILES = get_config()["tts"]["enable_cache"]
CACHED_AUDO_FILES_PATH = get_config()["tts"]["cache_directory"]


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

        if CACHE_GENERATED_AUDIO_FILES:
            file_path = os.path.join("/tmp", file_name)
        else:
            file_path = os.path.join(CACHED_AUDO_FILES_PATH, file_name)

        if CACHE_GENERATED_AUDIO_FILES and use_cache:
            if os.path.isfile(file_path):
                LOG.debug("Using cache file: %s" % (file_path))
                return file_path

        LOG.trace("Performing TTS on text \"%s\"" % (text))

        audio_file = gTTS(text=text,
                          lang="en-US",
                          slow=slow,
                          lang_check=False)

        audio_file.save(file_path)

        return file_path
