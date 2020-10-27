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
import tempfile
import unittest

from radio_bridge.rx import RX

from tests.unit.base import BaseTestCase

__all__ = ["RXTestCase"]


class RXTestCase(BaseTestCase):
    @unittest.skipIf(os.environ.get("CI"), "Skipping test on CI with no input devices")
    def test_record_audio(self):
        # NOTE: This test will fail if there is no input device detected on the system
        _, temp_path = tempfile.mkstemp()
        os.unlink(temp_path)

        self.assertFalse(os.path.isfile(temp_path))
        rx = RX(file_path=temp_path)
        rx.record_audio()
        self.assertTrue(os.path.isfile(temp_path))
