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

from raven.base import Client
from raven.utils.conf import convert_options
from raven.transport.http import HTTPTransport


logger = logging.getLogger('sentry.errors.client')


def configure_raven_client(config):
    # check for local environment
    defaults = {
        'include_paths': (
            set(config.get('SENTRY_INCLUDE_PATHS', []))
        ),
        'ignore_exceptions': config.get('RAVEN_IGNORE_EXCEPTIONS', []),
        'release': os.environ.get('SENTRY_RELEASE'),
        'environment': os.environ.get('SENTRY_ENVIRONMENT'),
        'tags': {
            'lambda': os.environ.get('AWS_LAMBDA_FUNCTION_NAME'),
            'version': os.environ.get('AWS_LAMBDA_FUNCTION_VERSION'),
            'memory_size': os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE'),
            'log_group': os.environ.get('AWS_LAMBDA_LOG_GROUP_NAME'),
            'log_stream': os.environ.get('AWS_LAMBDA_LOG_STREAM_NAME'),

            'region': os.environ.get('SERVERLESS_REGION') or os.environ.get('AWS_REGION')
        },
        'transport': HTTPTransport,
        'dsn': os.environ.get('SENTRY_DSN')
    }

    return Client(
        **convert_options(
            config,
            defaults=defaults
        )
    )


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