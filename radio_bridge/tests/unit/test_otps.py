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
import tempfile

import radio_bridge.configuration

from radio_bridge.otp import get_valid_otps
from radio_bridge.otp import write_otps_to_disk
from radio_bridge.otp import validate_otp
from radio_bridge.otp import generate_and_write_otps
from radio_bridge.otp import NUMBER_OF_UNUSED_OTPS

__all__ = ["OTPsTestCase"]

MOCK_OTPS = [
    "12345",
    "54321",
    "98989",
    "17171",
]


class OTPsTestCase(unittest.TestCase):
    def setUp(self):
        # Use unique file for admin_otps_file_path config option for each test case
        _, temp_path = tempfile.mkstemp()

        radio_bridge.configuration.CONFIG = {"plugins": {"admin_otps_file_path": temp_path}}

        self._db_path = temp_path

    def test_get_valid_otps(self):
        # File doesn't exist
        os.unlink(self._db_path)

        result = get_valid_otps()
        self.assertEqual(result, [])

        # Empty file
        self.setUp()

        result = get_valid_otps()
        self.assertEqual(result, [])

        # Write mock data and verify
        self._write_mock_otps()

        result = get_valid_otps()
        self.assertEqual(result, sorted(MOCK_OTPS))

    def test_validate_otp(self):
        self._write_mock_otps()

        # Invalid OTPs
        otp = MOCK_OTPS[0] + "1"
        result = validate_otp(otp)
        self.assertFalse(result)

        otp = "55555"
        result = validate_otp(otp)
        self.assertFalse(result)

        # Valid OTP
        otp = MOCK_OTPS[0]
        result = validate_otp(otp)
        self.assertTrue(result)
        self._assertOtpNotInFile(otp)

        otp = MOCK_OTPS[1]
        result = validate_otp(otp)
        self.assertTrue(result)
        self._assertOtpNotInFile(otp)

        # Verify OTPs have been revoked
        valid_ots = get_valid_otps()
        self.assertEqual(len(valid_ots), len(MOCK_OTPS) - 2)

    def test_generate_and_write_ops_initial_empty_file(self):
        all_otps, new_otps = generate_and_write_otps()
        self.assertEqual(len(all_otps), NUMBER_OF_UNUSED_OTPS)
        self.assertEqual(len(new_otps), NUMBER_OF_UNUSED_OTPS)
        self.assertEqual(all_otps, new_otps)

    def test_generate_and_write_ops_file_already_exists(self):
        self._write_mock_otps()
        all_otps, new_otps = generate_and_write_otps()
        self.assertEqual(len(all_otps), NUMBER_OF_UNUSED_OTPS)
        self.assertEqual(len(new_otps), NUMBER_OF_UNUSED_OTPS - len(MOCK_OTPS))

    def _assertOtpNotInFile(self, otp: str) -> None:
        with open(self._db_path, "r") as fp:
            content = fp.read()

        if otp in content:
            self.fail("OTP %s found in file" % (otp))

    def _write_mock_otps(self):
        write_otps_to_disk(otps=MOCK_OTPS)
