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

import abc
import wave

import structlog
import numpy as np

from scipy.io import wavfile

LOG = structlog.getLogger(__name__)

# Maps DTMF character to frequency boundaries
DTMF_TABLE_HIGH_LOW = {
    "1": [1209, 697],
    "2": [1336, 697],
    "3": [1477, 697],
    "A": [1633, 697],
    "4": [1209, 770],
    "5": [1336, 770],
    "6": [1477, 770],
    "B": [1633, 770],
    "7": [1209, 852],
    "8": [1336, 852],
    "9": [1477, 852],
    "C": [1633, 852],
    "*": [1209, 941],
    "0": [1336, 941],
    "#": [1477, 941],
    "D": [1633, 941],
}

DTMF_TABLE_LOW_HIGH = {
    (697, 1209): "1",
    (697, 1336): "2",
    (697, 1477): "3",
    (770, 1209): "4",
    (770, 1336): "5",
    (770, 1477): "6",
    (852, 1209): "7",
    (852, 1336): "8",
    (852, 1477): "9",
    (941, 1209): "*",
    (941, 1336): "0",
    (941, 1477): "#",
    (697, 1633): "A",
    (770, 1633): "B",
    (852, 1633): "C",
    (941, 1633): "D",
}


class BaseDTMFDecoderImplementation(object):
    def __init__(self, file_path: str = "/tmp/recording.wav", **implementation_kwargs: Any):
        self._file_path = file_path

    @abc.abstractmethod
    def decode(self) -> str:
        pass

    def _get_sample_rate(self):
        """
        Return sample (frame) rate for the input file.
        """
        with wave.open(self._file_path, "r") as wav:
            (_, _, sample_rate, _, _, _) = wav.getparams()

        return sample_rate


class FFTDTMFDecoderImplementation(BaseDTMFDecoderImplementation):
    # Based on https://github.com/ribt/dtmf-decoder

    def __init__(
        self,
        file_path: str = "/tmp/recording.wav",
        acceptable_error: int = 20,
        process_intervals: float = 0.05,
    ):
        """
        :param acceptable_error. Acceptable frequency error in hertz.
        :param process_intervals: Process in <x> second intervals.
        """
        super(FFTDTMFDecoderImplementation, self).__init__(file_path=file_path)

        self._acceptable_error = acceptable_error
        self._process_intervals = process_intervals

    def decode(self, return_on_first_char: bool = True) -> str:
        fps, data = wavfile.read(self._file_path, "rb")

        assert len(data.shape) == 1, "input is not mono"

        precision = self._process_intervals
        duration = len(data) / fps
        step = int(len(data) // (duration // precision))

        result = ""
        char = ""

        for i in range(0, len(data) - step, step):
            signal = data[i : i + step]

            fourier = np.fft.fft(signal)
            frequencies = np.fft.fftfreq(signal.size, d=1 / fps)

            # Low
            debut = np.where(frequencies > 0)[0][0]
            fin = np.where(frequencies > 1050)[0][0]

            freq = frequencies[debut:fin]
            amp = abs(fourier.real[debut:fin])

            lf = freq[np.where(amp == max(amp))[0][0]]

            delta = self._acceptable_error
            best = 0

            for f in [697, 770, 852, 941]:
                if abs(lf - f) < delta:
                    delta = abs(lf - f)
                    best = f

            lf = best

            # High
            debut = np.where(frequencies > 1100)[0][0]
            fin = np.where(frequencies > 2000)[0][0]

            freq = frequencies[debut:fin]
            amp = abs(fourier.real[debut:fin])

            hf = freq[np.where(amp == max(amp))[0][0]]

            delta = self._acceptable_error
            best = 0

            for f in [1209, 1336, 1477, 1633]:
                if abs(hf - f) < delta:
                    delta = abs(hf - f)
                    best = f

            hf = best

            if lf == 0 or hf == 0:
                char = ""
            elif DTMF_TABLE_LOW_HIGH[(lf, hf)] != char:
                char = DTMF_TABLE_LOW_HIGH[(lf, hf)]
                result += char

                if return_on_first_char:
                    return result

        return result


class DTMFDecoder(object):

    implementations = {
        "fft": FFTDTMFDecoderImplementation,
    }

    def __init__(
        self,
        file_path: str = "/tmp/recording.wav",
        implementation: str = "fft",
        **implementation_kwargs: Any,
    ):
        self._file_path = file_path
        self._implementation = implementation
        self._implementation_kwargs = implementation_kwargs

        if implementation not in self.implementations:
            raise ValueError(
                "Invalid implementation: %s. Valid implementation are: %s"
                % (implementation, ",".join(self.implementations))
            )

        self._decoder = self.implementations[implementation](
            file_path=file_path, **self._implementation_kwargs
        )

    def decode(self, return_on_first_char: bool = True) -> str:
        """
        :param return_on_first_char: True if we should return on a first matching character instead
                                     of processing the whole sequence.
        """
        return self._decoder.decode(return_on_first_char=return_on_first_char)
