from typing import Any

import os
import abc
import hashlib

import structlog

from radio_bridge.configuration import get_config

LOG = structlog.getLogger(__name__)

CACHE_GENERATED_AUDIO_FILES = get_config()["tts"]["enable_cache"]
CACHED_AUDO_FILES_PATH = get_config()["tts"]["cache_directory"]


class BaseTextToSpeechImplementation(object):
    """
    Base class for all the TTS implementations.
    """

    implementation_id: str
    file_extension: str

    @abc.abstractmethod
    def text_to_speech(self, text: str, slow: bool = False, use_cache: bool = True) -> str:
        """
        Perform tts on the provided text string and write result to a file.
        """
        pass

    def _get_cache_file_path(self, text: str, use_cache: bool) -> str:
        """
        Return file path to where the synthesized audio file will be saved / cached, if cache is
        enabled, otherwise return random file path.
        """
        # TODO: Add cron job which auto purges old recording cached files
        file_hash = hashlib.md5(
            text.encode("utf-8") + self.implementation_id.encode("utf-8")
        ).hexdigest()
        file_name = "%s%s" % (file_hash, self.file_extension)

        if CACHE_GENERATED_AUDIO_FILES:
            file_path = os.path.join(CACHED_AUDO_FILES_PATH, file_name)
        else:
            file_path = os.path.join("/tmp", file_name)

        if CACHE_GENERATED_AUDIO_FILES and use_cache:
            if os.path.isfile(file_path):
                LOG.debug("Using cache file: %s" % (file_path))
                return file_path

        return file_path


class ESpeakTextToSpeech(BaseTextToSpeechImplementation):
    """
    Text To Speech implementation based on offline Espeak NG.

    This implementation doesn't need internet connection and only requires espeak system package to
    be installed.
    """

    implementation_id = "espeak"
    file_extension = ".wav"

    def text_to_speech(self, text: str, slow: bool = False, use_cache: bool = True) -> str:
        # TODO: Allow various settings to be changed via config option
        from espeakng import ESpeakNG

        file_path = self._get_cache_file_path(text=text, use_cache=use_cache)

        if CACHE_GENERATED_AUDIO_FILES and use_cache and os.path.isfile(file_path):
            LOG.debug("Using existing cached file: %s" % (file_path))

        LOG.trace('Performing TTS on text "%s" and saving result to %s' % (text, file_path))

        esng = ESpeakNG()
        esng.voice = "en-us"
        esng.pitch = 32
        esng.speed = 150

        wave_data = esng.synth_wav(text)

        with open(file_path, "wb") as fp:
            fp.write(wave_data)

        return file_path


class GoogleTextToSpeech(BaseTextToSpeechImplementation):
    """
    Text To Speech implementation based on online Google gTTS.

    This implementation requires internet access.
    """

    implementation_id = "gtts"
    file_extension = ".mp3"

    def text_to_speech(self, text: str, slow: bool = False, use_cache: bool = True) -> str:
        from gtts import gTTS

        file_path = self._get_cache_file_path(text=text, use_cache=use_cache)

        if CACHE_GENERATED_AUDIO_FILES and use_cache and os.path.isfile(file_path):
            LOG.debug("Using existing cached file: %s" % (file_path))
            return file_path

        LOG.trace('Performing TTS on text "%s" and saving result to %s' % (text, file_path))

        audio_file = gTTS(text=text, lang="en-US", slow=slow, lang_check=False)
        audio_file.save(file_path)

        return file_path


class TextToSpeech(object):
    implementations = {"gtts": GoogleTextToSpeech, "espeak": ESpeakTextToSpeech}

    def __init__(
        self,
        implementation: str = "gtts",
        **implementation_kwargs: Any,
    ):
        os.makedirs(CACHED_AUDO_FILES_PATH, exist_ok=True)

        self._implementation = implementation
        self._implementation_kwargs = implementation_kwargs

        if implementation not in self.implementations:
            raise ValueError(
                "Invalid implementation: %s. Valid implementation are: %s"
                % (implementation, ",".join(self.implementations))
            )

        self._tts = self.implementations[implementation](**self._implementation_kwargs)

    def text_to_speech(self, text: str, slow: bool = False, use_cache: bool = True) -> str:
        return self._tts.text_to_speech(text=text, slow=slow, use_cache=use_cache)
