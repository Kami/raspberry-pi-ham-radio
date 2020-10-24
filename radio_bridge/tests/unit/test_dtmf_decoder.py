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
import unittest

from radio_bridge.dtmf import FFTDTMFDecoderImplementation

__all__ = ["TestFFTDTMFDecoder"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../fixtures/dtmf"))


class TestFFTDTMFDecoder(unittest.TestCase):
    def test_decode_anytone_578_dtmf_data(self):
        values = [
            ("1.wav", "1"),
            ("2.wav", "2"),
            ("3.wav", "3"),
            ("4.wav", "4"),
            ("5.wav", "5"),
            ("6.wav", "6"),
            ("7.wav", "7"),
            ("8.wav", "8"),
            ("9.wav", "9"),
            ("*.wav", "*"),
            ("0.wav", "0"),
            ("#.wav", "#"),
        ]

        for file_path, expected_code in values:
            file_path = os.path.join(FIXTURES_DIR, "anytone_578/", file_path)
            decoder = FFTDTMFDecoderImplementation(file_path=file_path)
            self.assertEqual(decoder.decode(), expected_code)

    def test_decode_audio_check_tone_generator_data(self):
        values = [
            ("audiocheck.net_dtmf_1.wav", "1"),
            ("audiocheck.net_dtmf_2.wav", "2"),
            ("audiocheck.net_dtmf_3.wav", "3"),
            ("audiocheck.net_dtmf_4.wav", "4"),
            ("audiocheck.net_dtmf_5.wav", "5"),
            ("audiocheck.net_dtmf_6.wav", "6"),
            ("audiocheck.net_dtmf_7.wav", "7"),
            ("audiocheck.net_dtmf_8.wav", "8"),
            ("audiocheck.net_dtmf_9.wav", "9"),
            ("audiocheck.net_dtmf_*.wav", "*"),
            ("audiocheck.net_dtmf_0.wav", "0"),
            ("audiocheck.net_dtmf_#.wav", "#"),
        ]

        for file_path, expected_code in values:
            file_path = os.path.join(FIXTURES_DIR, "audiochecknet/", file_path)
            decoder = FFTDTMFDecoderImplementation(file_path=file_path)
            self.assertEqual(decoder.decode(), expected_code)
