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

from typing import Any

import os
import abc
import hashlib

import structlog
import requests

from radio_bridge.configuration import get_config_option

LOG = structlog.getLogger(__name__)


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

        cache_generated_audio_files = get_config_option(
            "tts", "enable_cache", "bool", fallback=False
        )

        if cache_generated_audio_files:
            cached_audio_files_path = get_config_option("tts", "cache_directory")
            file_path = os.path.join(cached_audio_files_path, file_name)
        else:
            file_path = os.path.join("/tmp", file_name)

        if self._is_valid_cached_file(file_path=file_path, use_cache=use_cache):
            return file_path

        return file_path

    def _is_valid_cached_file(self, file_path: str, use_cache: bool = True):
        cache_generated_audio_files = get_config_option(
            "tts", "enable_cache", "bool", fallback=False
        )

        if not cache_generated_audio_files or not use_cache:
            return False

        return os.path.isfile(file_path) and os.stat(file_path).st_size > 0


class ESpeakTextToSpeech(BaseTextToSpeechImplementation):
    """
    Text To Speech implementation based on offline Espeak NG.

    This implementation doesn't need internet connection and only requires espeak system package to
    be installed.
    """

    implementation_id = "espeak"
    file_extension = ".wav"
    supported_languages = ["en_US"]

    def text_to_speech(self, text: str, slow: bool = False, use_cache: bool = True) -> str:
        # TODO: Allow various settings to be changed via config option
        from espeakng import ESpeakNG

        file_path = self._get_cache_file_path(text=text, use_cache=use_cache)

        if self._is_valid_cached_file(file_path=file_path, use_cache=use_cache):
            LOG.debug("Using existing cached file: %s" % (file_path))
            return file_path

        LOG.trace('Performing TTS on text "%s" and saving result to %s' % (text, file_path))

        esng = ESpeakNG()
        esng.voice = "en-us"
        esng.pitch = 32
        esng.pitch = 32

        if slow:
            esng.speed = 80
        else:
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
    supported_languages = ["en_US"]

    def text_to_speech(self, text: str, slow: bool = False, use_cache: bool = True) -> str:
        from gtts import gTTS

        file_path = self._get_cache_file_path(text=text, use_cache=use_cache)

        if self._is_valid_cached_file(file_path=file_path, use_cache=use_cache):
            LOG.debug("Using existing cached file: %s" % (file_path))
            return file_path

        LOG.trace('Performing TTS on text "%s" and saving result to %s' % (text, file_path))

        lang = "en-US"

        # Sometimes API returns "Unable to find token seed" error so we retry up to 3 times
        for i in range(0, 3):
            try:
                audio_file = gTTS(text=text, lang=lang, slow=slow, lang_check=False)
                audio_file.save(file_path)
                break
            except ValueError as e:
                if "Unable to find token seed" not in str(e):
                    raise e

                LOG.debug("Retrying gtts call due to failure: %s" % (str(e)))

        if not os.path.isfile(file_path) or os.stat(file_path).st_size == 0:
            LOG.error('Failed to perform TTS on text "%s"' % (text))
            return ""

        return file_path


class GovornikTextToSpeech(BaseTextToSpeechImplementation):
    implementation_id = "govornik"
    file_extension = ".wav"
    supported_languages = ["sl_SI"]

    def text_to_speech(self, text: str, slow: bool = False, use_cache: bool = True) -> str:
        file_path = self._get_cache_file_path(text=text, use_cache=use_cache)

        if self._is_valid_cached_file(file_path=file_path, use_cache=use_cache):
            LOG.debug("Using existing cached file: %s" % (file_path))
            return file_path

        LOG.trace('Performing TTS on text "%s" and saving result to %s' % (text, file_path))

        url = "http://sintetizator.nikigre.si"
        data = {
            "text": text,
            "voice": "nik-unit",
            "version": "2",
            "source": "radio_bridge",
            "format": "wav",
        }
        resp = requests.post(url=url, data=data)

        if resp.status_code != 200:
            LOG.warning("Received invalid status code (%s): %s." % (resp.status_code, resp.text))

        with open(file_path, "wb") as fp:
            for chunk in resp.iter_content(chunk_size=4096):
                fp.write(chunk)

        return file_path


class TextToSpeech(object):
    implementations = {
        "gtts": GoogleTextToSpeech,
        "espeak": ESpeakTextToSpeech,
        "govornik": GovornikTextToSpeech,
    }

    def __init__(
        self,
        implementation: str = "gtts",
        **implementation_kwargs: Any,
    ):
        cache_generated_audio_files = get_config_option(
            "tts", "enable_cache", "bool", fallback=False
        )
        cached_audio_files_path = get_config_option("tts", "cache_directory", "str", fallback=None)

        if cache_generated_audio_files:
            os.makedirs(cached_audio_files_path, exist_ok=True)

        self._implementation = implementation
        self._implementation_kwargs = implementation_kwargs

        if implementation not in self.implementations:
            raise ValueError(
                "Invalid implementation: %s. Valid implementation are: %s"
                % (implementation, ",".join(self.implementations))
            )

        self._tts = self.implementations[implementation]()  # type: ignore

    def text_to_speech(
        self, text: str, language: str = "en_US", slow: bool = False, use_cache: bool = True
    ) -> str:
        tts = self._get_tts_implementation_for_language(language=language)
        return tts.text_to_speech(text=text, slow=slow, use_cache=use_cache)

    def _get_tts_implementation_for_language(self, language: str) -> BaseTextToSpeechImplementation:
        if language == "sl_SI":
            return self.implementations["govornik"]()  # type: ignore
        elif language == "en_US":
            if "en_US" in self._tts.supported_languages:  # type: ignore
                return self._tts
            else:
                return self.implementations["espeak"]()  # type: ignore
        else:
            return self._tts  # type: ignore
