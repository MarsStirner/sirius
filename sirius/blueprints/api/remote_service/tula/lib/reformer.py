#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tula.active.card.reformer_builder import \
    CardTulaBuilder
from sirius.blueprints.api.remote_service.tula.active.checkup_first_ticket25.reformer_builder import \
    CheckupFirstTicket25TulaBuilder as ActCheckupFirstTicket25TulaBuilder
from sirius.blueprints.api.remote_service.tula.active.checkup_second_ticket25.reformer_builder import \
    CheckupSecondTicket25TulaBuilder as ActCheckupSecondTicket25TulaBuilder
from sirius.blueprints.api.remote_service.tula.active.checkup_pc_ticket25.reformer_builder import \
    CheckupPCTicket25TulaBuilder as ActCheckupPCTicket25TulaBuilder
from sirius.blueprints.api.remote_service.tula.active.epicrisis.reformer_builder import \
    EpicrisisTulaBuilder
from sirius.blueprints.api.remote_service.tula.active.measures.reformer_builder import \
    MeasureTulaBuilder
from sirius.blueprints.api.remote_service.tula.active.schedule.reformer_builder import \
    ScheduleTulaBuilder
from sirius.blueprints.api.remote_service.tula.active.schedule_ticket.reformer_builder import \
    ScheduleTicketTulaBuilder
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.api.remote_service.tula.passive.checkup_first_ticket25.reformer_builder import \
    CheckupFirstTicket25TulaBuilder as PassCheckupFirstTicket25TulaBuilder
from sirius.blueprints.api.remote_service.tula.passive.checkup_second_ticket25.reformer_builder import \
    CheckupSecondTicket25TulaBuilder as PassCheckupSecondTicket25TulaBuilder
from sirius.blueprints.api.remote_service.tula.passive.checkup_pc_ticket25.reformer_builder import \
    CheckupPCTicket25TulaBuilder as PassCheckupPCTicket25TulaBuilder
from sirius.blueprints.api.remote_service.tula.passive.childbirth.reformer_builder import \
    ChildbirthTulaBuilder
from sirius.blueprints.api.remote_service.tula.passive.client.reformer_builder import \
    ClientTulaBuilder
from sirius.blueprints.api.remote_service.tula.passive.doctor.reformer_builder import \
    DoctorTulaBuilder
from sirius.blueprints.api.remote_service.tula.passive.hospitalization.reformer_builder import \
    HospitalizationTulaBuilder
from sirius.blueprints.api.remote_service.tula.passive.organization.reformer_builder import \
    OrganizationTulaBuilder
from sirius.blueprints.api.remote_service.tula.passive.refbook.reformer_builder import \
    RefbookTulaBuilder
from sirius.blueprints.api.remote_service.tula.passive.research.reformer_builder import \
    ResearchTulaBuilder
from sirius.blueprints.api.remote_service.tula.passive.specialists_checkup.reformer_builder import \
    SpecialistsCheckupTulaBuilder
from sirius.blueprints.monitor.exception import InternalError, module_entry
from sirius.blueprints.reformer.api import Reformer
from sirius.blueprints.reformer.models.method import ServiceMethod
from sirius.lib.message import Message
from sirius.models.system import SystemCode


class TulaReformer(Reformer):
    remote_sys_code = SystemCode.TULA
    local_version = '0'
    remote_version = '0'

    ##################################################################
    ##  reform entities

    def get_local_entities(self, header_meta, data):
        remote_entity_code = header_meta['remote_entity_code']
        if remote_entity_code == TulaEntityCode.CLIENT:
            res = ClientTulaBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TulaEntityCode.ORGANIZATION:
            res = OrganizationTulaBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TulaEntityCode.DOCTOR:
            res = DoctorTulaBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TulaEntityCode.REFBOOK:
            res = RefbookTulaBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TulaEntityCode.MEASURE_SPECIALISTS_CHECKUP:
            res = SpecialistsCheckupTulaBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TulaEntityCode.MEASURE_HOSPITALIZATION:
            res = HospitalizationTulaBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TulaEntityCode.MEASURE_RESEARCH:
            res = ResearchTulaBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TulaEntityCode.CHILDBIRTH:
            res = ChildbirthTulaBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TulaEntityCode.CHECKUP_OBS_FIRST_TICKET:
            res = PassCheckupFirstTicket25TulaBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TulaEntityCode.CHECKUP_OBS_SECOND_TICKET:
            res = PassCheckupSecondTicket25TulaBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TulaEntityCode.CHECKUP_PC_TICKET:
            res = PassCheckupPCTicket25TulaBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TulaEntityCode.SCHEDULE:
            res = ScheduleTulaBuilder(self).build_local_entities(header_meta, data)
        else:
            raise InternalError('Unexpected remote_entity_code')
        return res

    def get_remote_entities(self, header_meta, data):
        local_entity_code = header_meta['local_entity_code']
        if local_entity_code == RisarEntityCode.SCHEDULE_TICKET:
            res = ScheduleTicketTulaBuilder(self).build_remote_entities(header_meta, data)
        elif local_entity_code == RisarEntityCode.CARD:
            res = CardTulaBuilder(self).build_remote_entities(header_meta, data)
        elif local_entity_code == RisarEntityCode.CHECKUP_OBS_FIRST_TICKET:
            res = ActCheckupFirstTicket25TulaBuilder(self).build_remote_entities(header_meta, data)
        elif local_entity_code == RisarEntityCode.CHECKUP_OBS_SECOND_TICKET:
            res = ActCheckupSecondTicket25TulaBuilder(self).build_remote_entities(header_meta, data)
        elif local_entity_code == RisarEntityCode.CHECKUP_PC_TICKET:
            res = ActCheckupPCTicket25TulaBuilder(self).build_remote_entities(header_meta, data)
        elif local_entity_code == RisarEntityCode.MEASURE:
            res = MeasureTulaBuilder(self).build_remote_entities(header_meta, data)
        elif local_entity_code == RisarEntityCode.EPICRISIS:
            res = EpicrisisTulaBuilder(self).build_remote_entities(header_meta, data)
        else:
            raise InternalError('Unexpected local_entity_code')
        return res

    ##################################################################
    ##  reform requests

    def get_remote_request(self, header_meta):
        remote_entity_code = header_meta.get('remote_entity_code')
        local_entity_code = header_meta.get('local_entity_code')
        if local_entity_code == RisarEntityCode.SCHEDULE or remote_entity_code == TulaEntityCode.SCHEDULE:
            data_req = ScheduleTulaBuilder(self).build_remote_request(header_meta, TulaEntityCode.SCHEDULE)
        else:
            raise InternalError('Unexpected local_entity_code (%s)' % local_entity_code)
        self.set_remote_request_params(data_req)
        self.set_request_service(data_req)
        return data_req

    ##################################################################
    ##  build packages

    @module_entry
    def get_entity_package_by_msg(self, msg):
        assert isinstance(msg, Message)

        meta = msg.get_header().meta
        serv_method = ServiceMethod.get_entity(meta['local_service_code'])
        src_system_code = serv_method['system_code']
        src_entity = serv_method['entity_code']
        meta['local_entity_code'] = src_entity
        if src_entity == RisarEntityCode.SCHEDULE_TICKET:
            res = ScheduleTicketTulaBuilder(self).build_local_entity_packages(msg)
        elif src_entity == RisarEntityCode.CARD:
            res = CardTulaBuilder(self).build_local_entity_packages(msg)
        elif src_entity == RisarEntityCode.CHECKUP_OBS_FIRST_TICKET:
            res = ActCheckupFirstTicket25TulaBuilder(self).build_local_entity_packages(msg)
        elif src_entity == RisarEntityCode.CHECKUP_OBS_SECOND_TICKET:
            res = ActCheckupSecondTicket25TulaBuilder(self).build_local_entity_packages(msg)
        elif src_entity == RisarEntityCode.CHECKUP_PC_TICKET:
            res = ActCheckupPCTicket25TulaBuilder(self).build_local_entity_packages(msg)
        elif src_entity == RisarEntityCode.MEASURE:
            res = MeasureTulaBuilder(self).build_local_entity_packages(msg)
        elif src_entity == RisarEntityCode.EPICRISIS:
            res = EpicrisisTulaBuilder(self).build_local_entity_packages(msg)
        else:
            raise InternalError('Unexpected entity code')
        return res

    @module_entry
    def get_entity_package_by_req(self, req):
        """
        Сбор сущностей в пакеты дозапросами. Сюда приходим из планировщика.

        Args:
            req: данные для запроса корневой сущности

        Returns: мета данные и пакеты сущностей
        """
        # todo: рассмотреть возможность использования MatchingEntity для автосборки пакетов
        meta = req.meta
        dst_entity = meta['dst_entity_code']
        if dst_entity == TulaEntityCode.SCHEDULE:
            res = ScheduleTulaBuilder(self).build_remote_entity_packages(req)
        else:
            raise InternalError('Unexpected dst_entity (%s)' % dst_entity)
        return res
