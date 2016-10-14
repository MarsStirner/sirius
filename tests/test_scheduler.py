#! coding:utf-8
"""


@author: BARS Group
@date: 05.10.2016

"""
from sirius.app import app
from sirius.blueprints.api.remote_service.consumer import RemoteConsumer
from sirius.blueprints.scheduler.api import Scheduler
from sirius.blueprints.scheduler.models import ScheduleGroup


class TestClient:

    def test_execute(self):
        with app.app_context():
            sch = Scheduler()
            # sch.execute()
            schedule_group = ScheduleGroup.query.first()
            for req_data in schedule_group.get_requests():
                msg = sch.create_message(req_data.entity.code)
                consumer = RemoteConsumer()
                consumer.process(msg, req_data.system.code)