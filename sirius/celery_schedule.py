from celery.schedules import crontab
import datetime

CELERYBEAT_SCHEDULE = {
    'schedule-every-five-minutes': {
        'task': 'sirius.lib.celery_tasks.scheduler_task',
        'schedule': datetime.timedelta(minutes=2),
    },
}
