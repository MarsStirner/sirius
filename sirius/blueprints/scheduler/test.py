#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from sirius.blueprints.api.remote_service.consumer import RemoteConsumer
from sirius.blueprints.monitor.exception import beat_entry
from sirius.blueprints.scheduler.api import Scheduler
from sirius.blueprints.scheduler.models import ScheduleGroup


class TestSchedule:

    @beat_entry
    def test_execute(self):
        with app.app_context():
            sch = Scheduler()
            schedule_group = ScheduleGroup.query.all()
            for req_data in schedule_group.get_requests():
                sch.execute(req_data)