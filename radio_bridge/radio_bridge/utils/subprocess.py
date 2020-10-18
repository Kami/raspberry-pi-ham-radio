# -*- coding: utf-8 -*-
# Copyright 2020 Tomaz Muraus
# Copyright 2019 Extreme Networks, Inc.
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

import signal

from ctypes import cdll

PR_SET_PDEATHSIG = 1


# This function is taken from StackStorm/st2 (ASF 2.0 license)
def on_parent_exit(signame):
    """
    Return a function to be run in a child process which will trigger SIGNAME to be sent when the
    parent process dies.

    Based on https://gist.github.com/evansd/2346614
    """

    def noop():
        pass

    try:
        libc = cdll["libc.so.6"]
    except OSError:
        # libc, can't be found (e.g. running on non-Unix system), we cant ensure signal will be
        # triggered
        return noop

    try:
        prctl = libc.prctl
    except AttributeError:
        # Function not available
        return noop

    signum = getattr(signal, signame)

    def set_parent_exit_signal():
        # http://linux.die.net/man/2/prctl
        result = prctl(PR_SET_PDEATHSIG, signum)
        if result != 0:
            raise Exception("prctl failed with error code %s" % result)

    return set_parent_exit_signal
