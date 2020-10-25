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
import re
import sys
import logging

from glob import glob
from os.path import splitext, basename, join as pjoin
from unittest import TextTestRunner, TestLoader

from setuptools import setup, find_packages

from distutils.core import Command
from setuptools import setup

from dist_utils import fetch_requirements
from dist_utils import get_version_string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS_FILE = os.path.join(BASE_DIR, "requirements.txt")
TESTS_REQUIREMENTS_FILE = os.path.join(BASE_DIR, "test-requirements.txt")

install_reqs, install_dep_links = fetch_requirements(REQUIREMENTS_FILE)
test_reqs, test_dep_links = fetch_requirements(TESTS_REQUIREMENTS_FILE)

sys.path.insert(0, BASE_DIR)

version = get_version_string(os.path.join(BASE_DIR, "wx_server/__init__.py"))


setup(
    name="wx-server",
    version=version,
    description=(
        "HTTP server for persisting weather station observarion in Ecowitt and Weather "
        "Underground format on disk"
    ),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Tomaz Muraus",
    author_email="tomaz@tomaz.me",
    license="Apache 2.0",
    url="https://github.com/Kami/raspberry-pi-ham-radio",
    include_package_data=True,
    packages=find_packages(exclude=["setuptools", "tests"]),
    provides=["wx_server"],
    install_requires=install_reqs,
    dependency_links=install_dep_links + test_dep_links,
    scripts=["bin/wx-server"],
    package_data={"wx_server": ["conf/*.conf"]},
    test_suite="tests",
    classifiers=[
        "Topic :: Communications :: Ham Radio",
        "Development Status :: 3 - Alpha" "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
