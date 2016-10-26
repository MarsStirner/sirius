#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.active.checkup_first.reformer_builder import \
    CheckupTambovBuilder
from sirius.blueprints.api.remote_service.tambov.active.patient.reformer_builder import \
    PatientTambovBuilder
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.monitor.exception import InternalError, module_entry
from sirius.blueprints.reformer.api import Reformer
from sirius.lib.remote_system import RemoteSystemCode


class TambovReformer(Reformer):
    remote_sys_code = RemoteSystemCode.TAMBOV

    ##################################################################
    ##  reform entities

    def get_local_entities(self, header_meta, data, addition_data):
        remote_entity_code = header_meta['remote_entity_code']
        if remote_entity_code == TambovEntityCode.PATIENT:
            res = PatientTambovBuilder(self.transfer, self.remote_sys_code).build_local_client(header_meta, data, addition_data)
        else:
            raise RuntimeError('Unexpected remote_entity_code')
        return res

    def get_remote_entities(self, header_meta, data, addition_data):
        local_entity_code = header_meta['local_entity_code']
        if local_entity_code == RisarEntityCode.CHECKUP_OBS_FIRST:
            res = CheckupTambovBuilder(self.transfer, self.remote_sys_code).build_remote_checkup(header_meta, data, addition_data)
        else:
            raise RuntimeError('Unexpected local_entity_code')
        return res

    ##################################################################
    ##  reform requests

    def get_remote_request(self, header_meta):
        remote_entity_code = header_meta['remote_entity_code']
        local_entity_code = header_meta['local_entity_code']
        if local_entity_code == RisarEntityCode.CLIENT or remote_entity_code == TambovEntityCode.PATIENT:
            req_data = PatientTambovBuilder(self.transfer, self.remote_sys_code).build_remote_patient_request(header_meta)
            self.set_remote_id(req_data)
            self.set_remote_service_request(req_data)
        else:
            raise RuntimeError('Unexpected local_entity_code')
        return req_data

    ##################################################################
    ##  build packages

    @module_entry
    def get_entity_packages(self, reformed_req):
        """
        Args:
            reformed_req: данные для запроса корневой сущности

        Returns: мета данные и пакеты сущностей

        Сбор сущностей в пакеты дозапросами.
        root_parent проставляется только для узла, у которого есть childs, но
        сам этот узел не корневой.
        is_changed - признак изменения пакета сущностей. ставится дефолт False

        entity_packages = {
            'system_code': self.remote_sys_code,
            'entities': {
                TambovEntityCode.PATIENT: [
                    {  # -> patient_node
                        'is_changed': False,
                        'main_id': patient_uid,
                        'data': {...},
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
        meta = reformed_req['meta']
        dst_entity = meta['dst_entity_code']
        # remote_entities = MatchingEntity.get_remote(
        #     src_entity, self.remote_sys_code
        # )
        # missing_entities = remote_entities - {dst_entity}
        if dst_entity == TambovEntityCode.PATIENT:
            res = PatientTambovBuilder(self.transfer, self.remote_sys_code).build_remote_patient_entity_packages(reformed_req)
        else:
            raise InternalError('Unexpected entity code')
        return res
