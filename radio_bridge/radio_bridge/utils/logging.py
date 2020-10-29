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

import logging

__all__ = ["set_log_level_for_all_loggers"]


# This function is taken from StackStorm/st2 (ASF 2.0 license)
# https://github.com/StackStorm/st2/blob/master/st2common/st2common/logging/misc.py
def set_log_level_for_all_handlers(logger, level=logging.DEBUG):
    """
    Set a log level for all the handlers on the provided logger.
    """
    logger.setLevel(level)

    handlers = logger.handlers
    for handler in handlers:
        handler.setLevel(level)

    return logger


# This function is taken from StackStorm/st2 (ASF 2.0 license)
# https://github.com/StackStorm/st2/blob/master/st2common/st2common/logging/misc.py
def set_log_level_for_all_loggers(level=logging.DEBUG):
    """
    Set a log level for all the loggers and handlers to the provided level.
    """
    root_logger = logging.getLogger()
    loggers = list(logging.Logger.manager.loggerDict.values())
    loggers += [root_logger]

    for logger in loggers:
        if isinstance(logger, logging.PlaceHolder):
            continue

        set_log_level_for_all_handlers(logger=logger, level=level)

    return loggers
