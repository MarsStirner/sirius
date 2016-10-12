# -*- coding: utf-8 -*-

from usagicompat import BIUsagiClient
from celery_schedule import CELERYBEAT_SCHEDULE
from celery_queue import get_celery_queues


class BICeleryUsagiClient(BIUsagiClient):
    def on_configuration(self, configuration):
        if 'SQLALCHEMY_ECHO' in configuration:
            configuration['SQLALCHEMY_ECHO'] = False
        # configuration['CELERYBEAT_SCHEDULE'] = CELERYBEAT_SCHEDULE
        configuration['CELERY_QUEUES'] = get_celery_queues(configuration)
        configuration['CELERYBEAT_SCHEDULE'] = CELERYBEAT_SCHEDULE

        super(BICeleryUsagiClient, self).on_configuration(configuration)
