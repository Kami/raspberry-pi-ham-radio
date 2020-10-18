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

import logging
import logging.config

import structlog


TRACE = logging.DEBUG - 1  # 10 - 1
AUDIT = logging.CRITICAL + 10  # 50 + 10


class ConsoleRendererWithCustomLogLevels(structlog.dev.ConsoleRenderer):
    @staticmethod
    def get_default_level_styles(colors=True):
        if colors:
            styles = structlog.dev._ColorfulStyles
        else:
            styles = structlog.dev._PlainStyles

        result = structlog.dev.ConsoleRenderer.get_default_level_styles(colors=colors)
        result["trace"] = styles.level_debug
        result["audit"] = styles.level_debug
        return result


def add_custom_log_levels():
    """
    Function which adds custom log levels to structlog.
    """
    # 1. TRACE
    structlog.stdlib.TRACE = TRACE
    structlog.stdlib._NAME_TO_LEVEL["trace"] = TRACE
    structlog.stdlib._LEVEL_TO_NAME[TRACE] = "trace"

    def trace(self, msg, *args, **kwargs):
        return self.log(TRACE, msg, *args, **kwargs)

    structlog.stdlib._FixedFindCallerLogger.trace = trace
    structlog.stdlib.BoundLogger.trace = trace

    logging.addLevelName(TRACE, "TRACE")

    # 2. AUDIT
    structlog.stdlib.TRACE = AUDIT
    structlog.stdlib._NAME_TO_LEVEL["audit"] = AUDIT
    structlog.stdlib._LEVEL_TO_NAME[AUDIT] = "audit"

    def audit(self, msg, *args, **kwargs):
        return self.log(AUDIT, msg, *args, **kwargs)

    structlog.stdlib._FixedFindCallerLogger.audit = audit
    structlog.stdlib.BoundLogger.audit = audit

    logging.addLevelName(AUDIT, "AUDIT")


def configure_logging(logging_config: str):
    add_custom_log_levels()

    logging.config.fileConfig(logging_config, disable_existing_loggers=False)

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S UTC", utc=True),
            ConsoleRendererWithCustomLogLevels(),
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,  # or OrderedDict if the runtime's dict is unordered (e.g. Python <3.6)
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
