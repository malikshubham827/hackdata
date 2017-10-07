"""
raven.contrib.lambda
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

from raven.base import Client
from raven.utils.conf import convert_options
from raven.transport.http import HTTPTransport
# from .utils import configure_raven_client, install_timers

logger = logging.getLogger('sentry.errors.client')


__all__ = 'sentry'


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


class Sentry(object):
    """
    Raven decorator for AWS Lambda.

    By default, the lambda integration will do the following:

    - Capture unhandled exceptions
    - Automatically create breadcrumbs

    Usage:

    from raven.contrib.aws_lambda import raven

    config = {
         'capture_errors': False,
         'capture_unhandled_rejections': True,
         'capture_memory_warnings': True,
         'capture_timeout_warnings': True
    }

    @raven
    def handler(event, context):
        raise Exception('I will be sent to sentry!')

    """

    def __init__(self, dsn=None, client=None, logging=True, breadcrumbs=True, **options):

        self.dsn = dsn
        self.logging = logging
        self.breadcrumbs = breadcrumbs
        self.client = client or make_client(options)

        if logging:
            setup_logging(SentryHandler(self.client))

    def __call__(self, fn):
        """Wraps our function with the necessary raven context."""

        #client = self
        #fn.func_defaults = (client,)

        @functools.wraps(fn)
        def decorated(client, event, context):
            raven_context = {
                'extra': {
                    'event': event,
                    'context': context,
                },
                'tags': {},
            }
            # Gather identity information from context if possible
            raven_context['user'] = self.get_identity(event)

            # Add additional tags for AWS_PROXY endpoints
            raven_context['tags']['aws_proxy'] = self.get_aws_proxy_context(event)

            # Add cloudwatch event context
            raven_context['tags']['cloudwatch_context'] = self.get_cloudwatch_event_context(event)

            # rethrow exception to halt lambda execution
            try:
                if self.config.get('auto_bread_crumbs'):
                    # first breadcrumb is the invocation of the lambda itself
                    breadcrumb = {
                        'message': os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'local'),
                        'category': 'lambda',
                        'level': 'info',
                        'data': {}
                    }

                    if event.get('requestContext'):
                        breadcrumb['data'] = {
                            'http_method': event['requestContext']['httpMethod'],
                            'host': event['headers']['Host'],
                            'path': event['path']
                        }

                    self.client.captureBreadcrumb(**breadcrumb)

                # invoke the original function
                return fn(event, context)
            except Exception as e:
                self.client.captureException()
                raise e

        return decorated

    @staticmethod
    def get_identity(event):
        if event.get('requestContext'):
            return {
                'api_id': event['requestContext']['apiId'],
                'api_stage': event['requestContext']['stage'],
                'http_method': event['requestContext']['httpMethod']
            }

    @staticmethod
    def get_cloudwatch_event_context(event):
        if event.get('detail'):
            context = {}
            if event.get('userIdentity'):
                context['cloudwatch_principal_id'] = event['userIdentity']['principalId']
            if event.get('awsRegion'):
                context['cloudwatch_region'] = event['awsRegion']
            return context if context else None

    @staticmethod
    def get_aws_proxy_context(event):
        if event.get('requestContext'):
            return {
                'api_id': event['requestContext']['apiId'],
                'api_stage': event['requestContext']['stage'],
                'http_method': event['requestContext']['httpMethod']
            }

sentry = Sentry
