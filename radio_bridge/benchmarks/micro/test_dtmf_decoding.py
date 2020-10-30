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

import pytest

from radio_bridge.dtmf import FFTDTMFDecoderImplementation

__all__ = ["test_benchmark_dtmf_decode_fft_algorithm"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../tests/fixtures/dtmf"))


@pytest.mark.benchmark(group="dtmf_decode")
@pytest.mark.parametrize(
    "data",
    [
        ("anytone_578/1.wav", "1"),
        ("anytone_578/2.wav", "2"),
        ("anytone_578/3.wav", "3"),
        ("anytone_578/4.wav", "4"),
        ("anytone_578/5.wav", "5"),
        ("anytone_578/6.wav", "6"),
        ("anytone_578/7.wav", "7"),
        ("anytone_578/8.wav", "8"),
        ("anytone_578/9.wav", "9"),
        ("anytone_578/*.wav", "*"),
        ("anytone_578/0.wav", "0"),
        ("anytone_578/#.wav", "#"),
    ],
    ids=[
        "anytone_578_digit_1",
        "anytone_578_digit_2",
        "anytone_578_digit_3",
        "anytone_578_digit_4",
        "anytone_578_digit_5",
        "anytone_578_digit_6",
        "anytone_578_digit_7",
        "anytone_578_digit_8",
        "anytone_578_digit_9",
        "anytone_578_digit_*",
        "anytone_578_digit_0",
        "anytone_578_digit_#",
    ],
)
def test_benchmark_dtmf_decode_fft_algorithm(benchmark, data):
    file_name, expected_sequence = data

    file_path = os.path.join(FIXTURES_DIR, file_name)
    decoder = FFTDTMFDecoderImplementation(file_path=file_path)

    def run_benchmark():
        return decoder.decode(return_on_first_char=True)

    result = benchmark.pedantic(run_benchmark, iterations=10, rounds=10)

    assert result == expected_sequence
