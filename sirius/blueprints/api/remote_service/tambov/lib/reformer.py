#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
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

    ##################################################################
    ##  reform entities

    def get_local_entities(self, header_meta, data, addition_data):
        remote_entity_code = header_meta['remote_entity_code']
        if remote_entity_code == TambovEntityCode.PATIENT:
            res = PatientTambovBuilder(self).build_local_entities(header_meta, data, addition_data)
        elif remote_entity_code == TambovEntityCode.SERVICE:
            res = ServiceTambovBuilder(self).build_local_measure(header_meta, data, addition_data)
        else:
            raise InternalError('Unexpected remote_entity_code')
        return res

    def get_remote_entities(self, header_meta, data, addition_data):
        local_entity_code = header_meta['local_entity_code']
        if local_entity_code == RisarEntityCode.CHECKUP_OBS_FIRST_TICKET:
            res = CaseTambovBuilder(self).build_remote_entities_first(header_meta, data, addition_data)
        elif local_entity_code == RisarEntityCode.CHECKUP_OBS_SECOND_TICKET:
            res = CaseTambovBuilder(self).build_remote_entities_second(header_meta, data, addition_data)
        elif local_entity_code == RisarEntityCode.MEASURE:
            res = ReferralTambovBuilder(self).build_remote_entities(header_meta, data, addition_data)
        else:
            raise InternalError('Unexpected local_entity_code')
        return res

    ##################################################################
    ##  reform requests

    def get_remote_request(self, header_meta):
        remote_entity_code = header_meta['remote_entity_code']
        local_entity_code = header_meta['local_entity_code']
        if local_entity_code == RisarEntityCode.CLIENT or remote_entity_code == TambovEntityCode.PATIENT:
            req_data = PatientTambovBuilder(self).build_remote_request(header_meta, TambovEntityCode.PATIENT)
            self.set_remote_request_params(req_data)
            self.set_request_service(req_data, self.remote_sys_code)
        elif local_entity_code in (
                RisarEntityCode.MEASURE_RESEARCH,
                RisarEntityCode.MEASURE_HOSPITALIZATION,
                RisarEntityCode.MEASURE_SPECIALISTS_CHECKUP,
        ) or remote_entity_code == TambovEntityCode.SERVICE:
            req_data = ServiceTambovBuilder(self).build_remote_request(header_meta, TambovEntityCode.SERVICE)
            self.set_remote_request_params(req_data)
            self.set_request_service(req_data, self.remote_sys_code)
        else:
            raise InternalError('Unexpected local_entity_code')
        return req_data

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
        Args:
            req: данные для запроса корневой сущности

        Returns: мета данные и пакеты сущностей

        Сбор сущностей в пакеты дозапросами.
        root_parent проставляется только для узла, у которого есть childs, но
        сам этот узел не корневой.
        is_changed - признак изменения пакета сущностей. ставится дефолт False
        entities - сущности, по которым будут независимые передачи
        addition - дополнительные данные (не дочерние), для построения запроса
        operation_code - результирующая операция. проставляется так же в diff
        main_param_name - для записи нового сопоставления ID

        entity_packages = {
            'system_code': self.remote_sys_code,
            'entities': {
                TambovEntityCode.PATIENT: [
                    {  # -> patient_node
                        'is_changed': False,
                        'operation_code': 'add',
                        'main_id': patient_uid,
                        *'main_param_name': '',
                        'data': {...},
                        'addition': {
                            TambovEntityCode.????: [
                                {
                                    'root_parent': patient_node,
                                    'method': req_data_method,
                                    'main_id': ind_addr_id,
                                    'data': {...},
                                }
                            ],
                        },
                        'childs': {
                            TambovEntityCode.IND_ADDRESS: [
                                {
                                    'root_parent': patient_node,
                                    'method': req_data_method,
                                    'main_id': ind_addr_id,
                                    'data': {...},
                                    'childs': {
                                        EntityCode...
                                    },
                                }
                            ],
                            TambovEntityCode.IND_DOCUMENTS: [
                                {
                                    'data': {...},
                                }
                            ],
                        },
                    },
                ],
            },
        }
        """
        # todo: вынести в ApiMethod доступ к параметрам, когда станет ясно как их лучше хранить
        # todo: рассмотреть возможность использования MatchingEntity для автосборки пакетов
        # todo: дозапросы будут переделаны в соответствии с новой wsdl
        meta = req['meta']
        dst_entity = meta['dst_entity_code']
        # remote_entities = MatchingEntity.get_remote(
        #     src_entity, self.remote_sys_code
        # )
        # missing_entities = remote_entities - {dst_entity}
        if dst_entity == TambovEntityCode.PATIENT:
            res = PatientTambovBuilder(self).build_remote_entity_packages(req)
        elif dst_entity == TambovEntityCode.SERVICE:
            res = ServiceTambovBuilder(self).build_remote_entity_packages(req)
        else:
            raise InternalError('Unexpected entity code')
        return res
