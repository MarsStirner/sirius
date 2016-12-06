# coding: utf-8
import logging

import os

from celery.utils.log import get_task_logger
from celery.signals import worker_process_init

from sirius.app import init_sirius_app
from sirius.extensions import db

from celeryusagicompat import BICeleryUsagiClient


logger = get_task_logger(__name__)
smp_logger = logging.getLogger('simple')

wsgi_app = init_sirius_app(BICeleryUsagiClient)


# https://github.com/Robpol86/Flask-Large-Application-Example
with wsgi_app.app_context():

    # Fix Flask-SQLAlchemy and Celery incompatibilities.
    @worker_process_init.connect
    def celery_worker_init_db(**_):
        """Initialize SQLAlchemy right after the Celery worker process forks.
        This ensures each Celery worker has its own dedicated connection to the MySQL database. Otherwise
        one worker may close the connection while another worker is using it, raising exceptions.
        Without this, the existing session to the MySQL server is cloned to all Celery workers, so they
        all share a single session. A SQLAlchemy session is not thread/concurrency-safe, causing weird
        exceptions to be raised by workers.
        Based on http://stackoverflow.com/a/14146403/1198943
        """
        logger.debug('Initializing SQLAlchemy for PID {}.'.format(os.getpid()))
        smp_logger.debug('Initializing SQLAlchemy for PID {}.'.format(os.getpid()))
        db.init_app(wsgi_app)


from sirius.extensions import celery  # this is what celery process uses
from sirius.lib.celery_tasks import *
