"""
raven.contrib.lambda.utils
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
# flake8: noqa

from __future__ import absolute_import

import os
import math
import psutil
import logging
from threading import Timer




logger = logging.getLogger('sentry.errors.client')





def timeout_error(config):
    """Captures a timeout error."""
    config['raven_client'].captureMessage('Function Timed Out', level='error')


def timeout_warning(config, context):
    """Captures a timeout warning."""
    config['raven_client'].captureMessage(
        'Function Execution Time Warning',
        level='warning',
        extra={
            'TimeRemainingInMsec': context.get_remaining_time_in_millis()

        }
    )


def memory_warning(config, context):
    """Determines when memory usage is nearing it's max."""
    used = psutil.Process(os.getpid()).memory_info().rss / 1048576
    limit = float(context.memory_limit_in_mb)
    p = used / limit

    if p >= 0.75:
        config['raven_client'].captureMessage(
            'Memory Usage Warning',
            level='warning',
            extra={
                'MemoryLimitInMB': context.memory_limit_in_mb,
                'MemoryUsedInMB': math.floor(used)
            }
        )
    else:
        # nothing to do check back later
        Timer(500, memory_warning, (config, context)).start()


def install_timers(config, context):
    """Create the timers as specified by the plugin configuration."""
    if config.get('capture_timeout_warnings'):
        # We schedule the warning at half the maximum execution time and
        # the error a few miliseconds before the actual timeout happens.
        time_remaining = context.get_remaining_time_in_millis()
        Timer(time_remaining / 2, timeout_warning, (config, context)).start()
        Timer(max(time_remaining - 500, 0), timeout_error, (config)).start()

    if config.get('capture_memory_warnings'):
        # Schedule the memory watch dog interval. Warning will re-schedule itself if necessary.
        Timer(500, memory_warning, (config, context)).start()