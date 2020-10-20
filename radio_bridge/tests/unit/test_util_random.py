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

import unittest

from radio_bridge.utils.random import generate_random_number

__all__ = ["RandomUtilTestCase"]


class RandomUtilTestCase(unittest.TestCase):
    def test_generate_random_number(self):
        # Verify that we don't generate a number where two neighboring dits are the same
        num_iterations = 5000

        for _ in range(num_iterations):
            result = generate_random_number(6)
            self.assertEqual(len(str(result)), 6)
            self._assertNeighboringDigitsAreDifferent(result)

        result = generate_random_number(6)
        self.assertEqual(len(str(result)), 6)

        result = generate_random_number(3)
        self.assertEqual(len(str(result)), 3)

    def test_assertNeighboringDigitsAreDifferent(self):
        valid_values = [1, 12, 123456789, 121521]

        for value in valid_values:
            result = self._assertNeighboringDigitsAreDifferent(value)
            self.assertTrue(result)

        invalid_values = [11, 122, 1233, 123455, 1111111]
        expected_msg = "neighboring digits which are the same"

        for value in invalid_values:
            self.assertRaisesRegex(
                AssertionError, expected_msg, self._assertNeighboringDigitsAreDifferent, value
            )

    def _assertNeighboringDigitsAreDifferent(self, value: int):
        for index, digit in enumerate((str(value)[1:])):
            if digit == str(value)[index]:
                self.fail("Value %s contains neighboring digits which are the same!" % (value))

        return True
