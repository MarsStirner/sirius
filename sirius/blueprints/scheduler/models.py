#! coding:utf-8
"""


@author: BARS Group
@date: 12.10.2016

"""
from contextlib import contextmanager
from datetime import datetime
from hashlib import md5

from hitsl_utils.enum import Enum
from sirius.database import Column, Model, db, reference_col, relationship
from sirius.extensions import cache
from sirius.models.entity import Entity
from sirius.models.system import System
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy.sql.elements import and_, or_
from sqlalchemy import case, cast


class ScheduleTimeType(Enum):
    DELTA = 1
    TIME = 2


class ScheduleTime(Model):
    """Периодичность расписания"""

    __tablename__ = 'schedule_time'

    code = Column(db.String(80), unique=True, nullable=False)
    type = Column(db.Integer, unique=False, nullable=False)  # ScheduleTimeType
    # date = Column(db.Date, unique=False, nullable=True)
    time = Column(db.Time, unique=False, nullable=False)

    # __table_args__ = (
    #     CheckConstraint("type = 1 OR type = 2 AND date is not null", name='_period_chk'),
    # )


class Schedule(Model):
    """
    Расписание запросов групп сущностей
    """
    # todo: зачем группы отвязаны от времени?

    __tablename__ = 'schedule'

    code = Column(db.String(80), unique=True, nullable=False)
    schedule_time_id = reference_col('schedule_time', unique=False, nullable=False)
    schedule_time = relationship('ScheduleTime', backref='set_schedule')
    schedule_group_id = reference_col('schedule_group', unique=False, nullable=False)
    schedule_group = relationship('ScheduleGroup', backref='set_sch_group_entity')

    __table_args__ = (
        UniqueConstraint('schedule_time_id', 'schedule_group_id', name='_sch_time_sch_group_uc'),
    )

    @classmethod
    def get_schedules_to_execute(cls):
        """Отбор расписаний, для которых есть подходящие по времени группы"""
        cur_datetime = datetime.today()
        cur_date = cur_datetime.date()
        cur_time = cur_datetime.time()
        last_execs_sq = db.session.query(SchGrReqExecute.begin_datetime).join(
            ScheduleGroupRequest, ScheduleGroupRequest.id == SchGrReqExecute.sch_group_request_id
        ).filter(
            ScheduleGroupRequest.schedule_group_id == ScheduleGroup.id,
        ).correlate(ScheduleGroup).order_by(
            SchGrReqExecute.id.desc()
        ).limit(1).subquery('sq')
        old_execs_q = db.session.query('1').filter(
            case([
                (
                    ScheduleTime.type == ScheduleTimeType.DELTA,
                    cur_datetime - last_execs_sq.c.begin_datetime > ScheduleTime.time
                ),
                (
                    ScheduleTime.type == ScheduleTimeType.TIME,
                    and_(
                        cur_time.isoformat() > ScheduleTime.time,
                        cur_date > cast(last_execs_sq.c.begin_datetime, db.Date)
                    )
                ),
            ]),
        ).correlate(ScheduleTime)
        one_exec_q = SchGrReqExecute.query.join(
            ScheduleGroupRequest, ScheduleGroupRequest.id == SchGrReqExecute.sch_group_request_id
        ).filter(
            ScheduleGroupRequest.schedule_group_id == ScheduleGroup.id
        ).correlate(ScheduleGroup).limit(1)
        res = cls.query.join(
            ScheduleTime, ScheduleTime.id == cls.schedule_time_id
        ).join(
            ScheduleGroup, ScheduleGroup.id == cls.schedule_group_id
        ).filter(
            or_(
                old_execs_q.exists() == True,
                one_exec_q.exists() == False,
            )
        ).all()
        return res

    @contextmanager
    def acquire_group_lock(self):
        lock_expire = 60*60*10  # 10h
        group_hexdigest = md5(self.schedule_group.code).hexdigest()
        lock_id = '{0}-lock-{1}'.format(self.__class__.__name__, group_hexdigest)

        def acquire_lock():
            # cache.add fails if the key already exists
            return cache.add(lock_id, 'true', lock_expire)

        def release_lock():
            cache.delete(lock_id)

        res = None
        try:
            res = acquire_lock()
            yield res
        finally:
            if res:
                release_lock()


class ScheduleGroup(Model):
    """Группы запросов сущностей"""

    __tablename__ = 'schedule_group'

    code = Column(db.String(80), unique=True, nullable=False)

    def get_requests(self):
        res = ScheduleGroupRequest.query.join(
            Entity, Entity.id == ScheduleGroupRequest.entity_id
        ).join(
            System, System.id == ScheduleGroupRequest.system_id
        ).filter(
            ScheduleGroupRequest.schedule_group_id == self.id,
            ScheduleGroupRequest.enabled == True,
        ).order_by(ScheduleGroupRequest.order).all()
        return res


class ScheduleGroupRequest(Model):
    """Данные запросов в группе"""

    __tablename__ = 'sch_group_request'

    schedule_group_id = reference_col('schedule_group', unique=False, nullable=False)
    schedule_group = relationship('ScheduleGroup', backref='set_sch_group_request')
    entity_id = reference_col('entity', unique=False, nullable=False)  # что
    entity = relationship('Entity', backref='set_sch_group_request')
    system_id = reference_col('system', unique=False, nullable=False)  # откуда
    system = relationship('System', backref='set_sch_group_request')
    sampling_method = Column(db.String(80), unique=False, nullable=True)
    order = Column(db.Integer, unique=False, nullable=False)
    enabled = Column(db.Boolean, unique=False, nullable=False, server_default='false')

    __table_args__ = (
        UniqueConstraint('schedule_group_id', 'entity_id', 'system_id', name='_sch_group_entity_system_uc'),
        UniqueConstraint('schedule_group_id', 'order', name='_sch_group_order_uc'),
    )


class SchGrReqExecute(Model):
    """История выполнения расписания запросов сущностей"""

    __tablename__ = 'sch_gr_req_execute'

    sch_group_request_id = reference_col('sch_group_request', unique=False, nullable=False)
    sch_group_request = relationship('ScheduleGroupRequest', backref='set_sch_gr_req_execute')
    begin_datetime = Column(db.DateTime, unique=False, nullable=False)
    end_datetime = Column(db.DateTime, unique=False, nullable=True)

    @classmethod
    def begin(cls, sch_group_request):
        res = cls.create(
            sch_group_request_id=sch_group_request.id,
            begin_datetime=datetime.today()
        )
        return res

    def end(self):
        self.update(
            end_datetime=datetime.today()
        )

    @classmethod
    def last_datetime(cls, local_entity_code):
        res = cls.query.join(
            ScheduleGroupRequest
        ).join(
            Entity
        ).filter(
            Entity.code == local_entity_code
        ).order_by(
            cls.id.desc()
        ).limit(1).first()
        return res and res.begin_datetime
