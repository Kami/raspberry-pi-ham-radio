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

from typing import List
from typing import Optional

import random

__all__ = ["generate_random_number"]


def generate_random_number(
    length: int = 6, forbidden_first_digit: Optional[List[int]] = None
) -> int:
    """
    Generate random number with the provided length (number of digits) ensuring that two neighboring
    digits are always different and with each digit having a value between 1 - 9.
    """
    result = ""

    while len(result) < length:
        random_value = random.randint(0, 9)

        if len(result) == 0:
            # First digit
            if forbidden_first_digit and random_value in forbidden_first_digit:
                continue

            result += str(random_value)
        else:
            # Make sure it's different than the previous digit
            if random_value == int(result[-1]):
                continue

            result += str(random_value)

    return int(result)
