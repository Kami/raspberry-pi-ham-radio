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

"""
Module with utility functions for generating, managing and verifying OTPs (One Time Pin) codes which
are used to execute admin commands / DTMF plugins.

Keep in mind that those OTPs are only meant as a very basic protection against unauthorized access
for non advanced users.

They are not meant as a 100% safe, robust and secure solution. As such, we store them in a plain
text format in a file on disk.
"""

from typing import List
from typing import Tuple

import os

import structlog

from radio_bridge.configuration import get_config
from radio_bridge.utils.random import generate_random_number

__all__ = ["generate_and_write_otps", "validate_otp", "get_valid_otps"]

LOG = structlog.getLogger(__name__)

# On server startup we will ensure there are always at least that many valid and unused OTPs
# available
NUMBER_OF_UNUSED_OTPS = 100

# How long should each OTP be
OTP_LENGTH = 4


def get_valid_otps() -> List[str]:
    """
    Return a list of all the OTPs which are still valid (unused) from a local db file on disk.
    """
    otps_file_path = get_config()["plugins"]["admin_otps_file_path"]

    valid_otps = []

    if otps_file_path and os.path.isfile(otps_file_path):
        with open(otps_file_path, "r") as fp:
            content = fp.read().strip()

        if content:
            valid_otps = content.splitlines()

    return sorted(valid_otps)


def write_otps_to_disk(otps: List[str]) -> bool:
    """
    Write provided OTPs to a local db file on disk, overwriting any existing content.
    """
    otps_file_path = get_config()["plugins"]["admin_otps_file_path"]

    otps = set(otps)

    with open(otps_file_path, "w") as fp:
        fp.write("\n".join(sorted(list(otps))))

    return True


def generate_and_write_otps() -> Tuple[List[str], List[str]]:
    """
    Generate random 4 digit numbers which can be used as one time password when executing admin
    commands and write them to a file on disk.

    Keep in mind that each of those numbers is only valid for a single use.
    """
    # 1. First check if file exists, if it does, read the existing values and generate any
    # new values which are needed to ensure there are always NUMBER_OF_UNUSED_OTPS unused
    # otps available in that file on server startup.
    existing_otps = get_valid_otps()

    if existing_otps:
        LOG.debug("Found and re-using %s existing unused OTPs from disk" % (len(existing_otps)))

    number_of_new_otps_to_generate = NUMBER_OF_UNUSED_OTPS - len(existing_otps)
    if number_of_new_otps_to_generate < 1:
        number_of_new_otps_to_generate = 0

    LOG.debug("Generating %s new OTPs" % (number_of_new_otps_to_generate))

    new_otps = set([])

    while len(new_otps) < number_of_new_otps_to_generate:
        value = generate_random_number(length=OTP_LENGTH, forbidden_first_digit=[0])
        new_otps.add(str(value))

    new_otps = sorted(new_otps)

    # Update the file / write all the active OTPs to disk
    all_otps = set()
    all_otps.update(existing_otps)
    all_otps.update(new_otps)
    all_otps = sorted(all_otps)

    write_otps_to_disk(all_otps)

    return list(all_otps), list(new_otps)


def validate_otp(otp: str) -> bool:
    """
    Check if the provided OTP is valid.

    If it is, True will be returned and this OTP will be marked as used (removed from a file) and
    as such, become invalid for future requests.
    """
    valid_otps = get_valid_otps()
    assert isinstance(valid_otps, list)

    otp_masked = otp[:2] + "*" * len(otp[2:])

    if otp in valid_otps:
        LOG.info("OTP %s has been successfully validated and revoked" % (otp_masked))
        valid_otps.remove(otp)
        write_otps_to_disk(valid_otps)
        return True

    LOG.info("OTP %s is not valid" % (otp_masked))
    return False
