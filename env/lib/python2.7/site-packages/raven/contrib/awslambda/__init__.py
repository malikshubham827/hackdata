"""
raven.contrib.awslambda
~~~~~~~~~~~~~~~~~~~~

Raven wrapper for AWS Lambda handlers.

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
# flake8: noqa

from __future__ import absolute_import

import os
import logging
import functools

from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler
from raven import breadcrumbs

from raven.base import Client
from raven.utils.conf import convert_options
from raven.transport.http import HTTPTransport

logger = logging.getLogger('sentry.errors.client')


__all__ = 'raven'


def make_client(config):
    defaults = {
        'ignore_exceptions': config.get('SENTRY_IGNORE_EXCEPTIONS', []),
        'release': os.environ.get('SENTRY_RELEASE'),
        'environment': os.environ.get('SENTRY_ENVIRONMENT'),
        'tags': {
            'lambda': os.environ.get('AWS_LAMBDA_FUNCTION_NAME'),
            'version': os.environ.get('AWS_LAMBDA_FUNCTION_VERSION'),
            'memory_size': os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE'),
            'log_group': os.environ.get('AWS_LAMBDA_LOG_GROUP_NAME'),
            'log_stream': os.environ.get('AWS_LAMBDA_LOG_STREAM_NAME'),
            'region': os.environ.get('AWS_REGION')
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


class Raven(object):
    """
    Raven decorator for AWS Lambda.

    By default, the lambda integration will capture unhandled exceptions and instrument logging.

    Usage:

    >>> from raven.contrib.aws_lambda import sentry
    >>>
    >>> @sentry
    >>> def handler(event, context):
    >>>    ...
    >>>    raise Exception('I will be sent to sentry!')


    If you want to add breadcrumbs, send messages or from within your handler,
    just add sentry to your function arguments:

    You can add extra context by calling `sentry.addContext`

    >>> sentry.addContext({'foo': 'bar'})

    """

    def __new__(cls, *args, **kwargs):
        """Hack allows cls decorator to be called analog to func decorators"""
        self = super().__new__(cls)

        if not kwargs and len(args) == 1 and callable(args[0]):
            self.__init__()
            return self(args[0])
        return self

    def __init__(self, dsn=None, client=None, logging=True, breadcrumbs=True, **kwargs):

        self.dsn = dsn
        self.logging = logging
        self.breadcrumbs = breadcrumbs
        self.client = client or make_client(kwargs)

        if logging:
            setup_logging(SentryHandler(self.client))

    def __call__(self, fn):
        """Wraps our function with the necessary raven context."""

        @functools.wraps(fn)
        def decorated(event, context):
            self.record_breadcrumb(data=context, level='debug')
            self.client.extra_context({
                'event': event,
                'aws_request_id': context.aws_request_id,
                'client_context': context.client_context,
                'identity': context.identity,
            })
            try:
                return fn(event, context)
            except Exception as e:
                self.client.captureException()
                self.client.context.clear()
                raise e

        return decorated

    @staticmethod
    def record_breadcrumb(*args, **kwargs):
        return breadcrumbs.record(*args, **kwargs)

raven = Raven
