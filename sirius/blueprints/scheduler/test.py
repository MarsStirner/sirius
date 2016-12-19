#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from sirius.blueprints.api.remote_service.consumer import RemoteConsumer
from sirius.blueprints.monitor.exception import beat_entry
from sirius.blueprints.scheduler.api import Scheduler
from sirius.blueprints.scheduler.models import ScheduleGroup, \
    ScheduleGroupRequest


class _TestSchedule:

    @beat_entry
    def test_execute(self):
        with app.app_context():
            sch = Scheduler()

            # sch.run()

            # schedule_groups = ScheduleGroup.query.all()
            # for schedule_group in schedule_groups:
            #     for req_data in schedule_group.get_requests():
            #         sch.execute(req_data)

            req_data = ScheduleGroupRequest.query.filter(
                # ScheduleGroupRequest.schedule_group_id == 1,
                # ScheduleGroupRequest.order == 1,  # getPatiients
                # ScheduleGroupRequest.order == 3,  # get_doctors
                # ScheduleGroupRequest.order == 4,  # get_measures_results
                # ScheduleGroupRequest.order == 5,  # get_hospital_rec
                # ScheduleGroupRequest.order == 6,  # send_exchange_card
                # ScheduleGroupRequest.order == 7,  # childbirth

                # ScheduleGroupRequest.schedule_group_id == 2,
                # ScheduleGroupRequest.order == 1,  # schedules
            ).one()
            sch.execute(req_data)
