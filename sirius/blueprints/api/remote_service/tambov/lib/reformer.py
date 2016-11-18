#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.active.clinic.reformer_builder import \
    ClinicTambovBuilder
from sirius.blueprints.reformer.models.method import ServiceMethod
from ..active.case.reformer_builder import CaseTambovBuilder
from ..active.patient.reformer_builder import PatientTambovBuilder
from ..active.service.reformer_builder import ServiceTambovBuilder
from ..active.referral.reformer_builder import ReferralTambovBuilder
from ..entities import TambovEntityCode
from sirius.blueprints.monitor.exception import InternalError, module_entry
from sirius.blueprints.reformer.api import Reformer
from sirius.lib.message import Message
from sirius.models.system import SystemCode


class TambovReformer(Reformer):
    remote_sys_code = SystemCode.TAMBOV
    local_version = '0'
    remote_version = '0'

    ##################################################################
    ##  reform entities

    def get_local_entities(self, header_meta, data):
        remote_entity_code = header_meta['remote_entity_code']
        if remote_entity_code == TambovEntityCode.PATIENT:
            res = PatientTambovBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TambovEntityCode.REFERRAL:
            res = ReferralTambovBuilder(self).build_local_entities(header_meta, data)
        elif remote_entity_code == TambovEntityCode.CLINIC:
            res = ClinicTambovBuilder(self).build_local_entities(header_meta, data)
        else:
            raise InternalError('Unexpected remote_entity_code')
        return res

    def get_remote_entities(self, header_meta, data):
        local_entity_code = header_meta['local_entity_code']
        if local_entity_code == RisarEntityCode.CHECKUP_OBS_FIRST_TICKET:
            res = CaseTambovBuilder(self).build_remote_entities_first(header_meta, data)
        elif local_entity_code == RisarEntityCode.CHECKUP_OBS_SECOND_TICKET:
            res = CaseTambovBuilder(self).build_remote_entities_second(header_meta, data)
        elif local_entity_code == RisarEntityCode.MEASURE:
            res = ReferralTambovBuilder(self).build_remote_entities(header_meta, data)
        else:
            raise InternalError('Unexpected local_entity_code')
        return res

    ##################################################################
    ##  reform requests

    def get_remote_request(self, header_meta):
        remote_entity_code = header_meta['remote_entity_code']
        local_entity_code = header_meta['local_entity_code']
        if local_entity_code == RisarEntityCode.CLIENT or remote_entity_code == TambovEntityCode.PATIENT:
            data_req = PatientTambovBuilder(self).build_remote_request(header_meta, TambovEntityCode.PATIENT)
        elif local_entity_code in (
                RisarEntityCode.MEASURE_RESEARCH,
                RisarEntityCode.MEASURE_HOSPITALIZATION,
                RisarEntityCode.MEASURE_SPECIALISTS_CHECKUP,
        ) or remote_entity_code == TambovEntityCode.SERVICE:
            data_req = ServiceTambovBuilder(self).build_remote_request(header_meta, TambovEntityCode.SERVICE)
        elif local_entity_code == RisarEntityCode.ORGANISATION or remote_entity_code == TambovEntityCode.CLINIC:
            data_req = ClinicTambovBuilder(self).build_remote_request(header_meta, TambovEntityCode.CLINIC)
        else:
            raise InternalError('Unexpected local_entity_code')
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
        if src_entity in (
            RisarEntityCode.CHECKUP_OBS_FIRST_TICKET,
            RisarEntityCode.CHECKUP_OBS_SECOND_TICKET,
        ):
            res = CaseTambovBuilder(self).build_local_entity_packages(msg)
        elif src_entity == RisarEntityCode.MEASURE:
            res = ReferralTambovBuilder(self).build_local_entity_packages(msg)
        else:
            raise InternalError('Unexpected entity code')
        return res

    @module_entry
    def get_entity_package_by_req(self, req):
        """
        Сбор сущностей в пакеты дозапросами.

        Args:
            req: данные для запроса корневой сущности

        Returns: мета данные и пакеты сущностей
        """
        # todo: рассмотреть возможность использования MatchingEntity для автосборки пакетов
        meta = req.meta
        dst_entity = meta['dst_entity_code']
        if dst_entity == TambovEntityCode.PATIENT:
            res = PatientTambovBuilder(self).build_remote_entity_packages(req)
        elif dst_entity == TambovEntityCode.SERVICE:
            res = ServiceTambovBuilder(self).build_remote_entity_packages(req)
        elif dst_entity == TambovEntityCode.CLINIC:
            res = ClinicTambovBuilder(self).build_remote_entity_packages(req)
        else:
            raise InternalError('Unexpected entity code')
        return res
