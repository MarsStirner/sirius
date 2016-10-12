#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from hitsl_utils.enum import Enum
from sirius.blueprints.remote_service.lib.reformer import Reformer
from sirius.blueprints.remote_service.models.matching import MatchingId
from sirius.blueprints.remote_service.models.method import ApiMethod
from sirius.lib.apiutils import ApiException
from sirius.lib.message import Message
from sirius.lib.remote_system import RemoteSystemCode
from sirius.models.entity import LocalEntityCode
from sirius.models.operation import OperationCode
from sirius.models.protocol import ProtocolCode


class RemoteEntityCode(Enum):
    PATIENT = 'Patient'
    IND_ADDRESS = 'IndividualAddress'
    IND_DOCUMENTS = 'IndividualDocument'

    CHECKUP = 'checkup'
    CHECKUP_FETUS = 'checkup_fetus'


class TambovReformer(Reformer):
    remote_sys_code = RemoteSystemCode.TAMBOV

    ##################################################################
    ##  reform entities

    def get_local_entities(self, header_meta, data, addition_data):
        remote_entity_code = header_meta['remote_entity_code']
        if remote_entity_code == RemoteEntityCode.PATIENT:
            res = self.build_local_client(header_meta, data, addition_data)
        else:
            raise RuntimeError('Unexpected remote_entity_code')
        return res

    def get_remote_entities(self, header_meta, data, addition_data):
        local_entity_code = header_meta['local_entity_code']
        if local_entity_code == LocalEntityCode.CHECKUP_OBS_FIRST:
            res = self.build_remote_checkup(header_meta, data, addition_data)
        else:
            raise RuntimeError('Unexpected local_entity_code')
        return res

    ##################################################################
    ##  reform entities checkup

    def build_remote_checkup(self, header_meta, data, addition_data):
        # todo:
        src_entity_code = db_get_local_entity_code(header_meta['local_service_code'])
        src_operation_code = self.get_operation_code_by_method(header_meta['local_method'])
        res = {
            'operation_order': {},
            RemoteEntityCode.CHECKUP: [{
                'meta': {
                    'src_entity_code': src_entity_code,
                    'src_id': header_meta['local_main_id'],
                    'dst_entity_code': RemoteEntityCode.CHECKUP,
                },
            }],
        }
        main_item = res[RemoteEntityCode.CHECKUP][0]
        if src_operation_code != OperationCode.DELETE:
            self.set_operation_order(res, RemoteEntityCode.CHECKUP, 1)
            main_item['body'] = {
                'code_1': data['code_1'],
                'code_2': addition_data['src_service_code']['code_2'],
            }
        else:
            self.set_operation_order(res, RemoteEntityCode.CHECKUP, 2)

        def set_parent_id(record):
            reform_meta = record['meta']
            parent_meta = reform_meta['parent_entity']['meta']
            reform_meta['dst_url'] = reform_meta['dst_url'].replace(
                parent_meta['dst_id_url_param_name'], parent_meta['dst_id']
            )
            record['body'] = {
                'parent_id': parent_meta['meta']['dst_id'],
            }
        for record in data['fetuses']:
            item = {
                'meta': {
                    'src_entity_code': src_entity_code,
                    'src_id': record['fetus_id'],
                    'dst_entity_code': RemoteEntityCode.CHECKUP_FETUS,
                    'set_parent_id_func': set_parent_id,
                    'parent_entity': main_item,
                },
            }
            res.setdefault(RemoteEntityCode.CHECKUP_FETUS, []).append(item)
            if src_operation_code != OperationCode.DELETE:
                self.set_operation_order(res, RemoteEntityCode.CHECKUP_FETUS, 2)
                item['body'] = {
                    'code_1': record['code_1'],
                    'code_2': addition_data['src_service_code']['code_2'],
                }
            else:
                self.set_operation_order(res, RemoteEntityCode.CHECKUP_FETUS, 1)
        return res

    ##################################################################
    ##  reform entities client

    def build_local_client(self, header_meta, entity_package, addition_data):
        patient_data = entity_package['data']
        src_entity_code = header_meta['remote_entity_code']

        def set_current_id_func(record):
            reform_meta = record['meta']
            record['body'] = {
                'client_id': reform_meta['meta']['dst_id'],
            }
        res = {
            'operation_order': {},
            LocalEntityCode.CLIENT: [{
                'meta': {
                    'src_entity_code': src_entity_code,
                    'src_id': header_meta['remote_main_id'],
                    'dst_entity_code': LocalEntityCode.CLIENT,
                    'set_current_id_func': set_current_id_func,
                },
            }],
        }
        main_item = res[LocalEntityCode.CLIENT][0]
        self.set_operation_order(res, LocalEntityCode.CLIENT, 1)
        main_item['body'] = {
            'client_id': None,  # заполняется в set_current_id_func
            'FIO': {
                'middlename': patient_data['middleName'],
                'name': patient_data['firstName'],
                'surname': patient_data['lastName']
            },
            'birthday_date': patient_data['birthDate'],
            'gender': patient_data['gender'],
            # необязательные
            'SNILS': None,  # заполняется в документах
        }
        childs = entity_package['childs']
        document_list = childs[RemoteEntityCode.IND_DOCUMENTS]
        for item in document_list:
            document_data = item['data']
            if document_data['type'] == '19':  # SNILS
                main_item['body']['SNILS'] = document_data['code']
            else:
                # todo: в схеме рисар document будет переделан на список documents
                main_item['body'].setdefault('documents', []).append({
                    'document_type_code': document_data['type'],
                    'document_number': document_data['number'],
                    'document_beg_date': document_data['activationDate'],
                    # необязательные
                    'document_series': document_data['series'],
                    'document_issuing_authority': document_data['issueOrganization'],
                })

        address_list = childs[RemoteEntityCode.IND_ADDRESS]
        for item in address_list:
            address_data = item['data']
            local_addr = {
                'KLADR_locality': None,  # заполняется в entry
                'KLADR_street': None,  # заполняется в entry
                'house': address_data['house'],
                'locality_type': address_data[''],
                # необязательные
                'building': address_data[''],
                'flat': address_data['apartment'],
            }
            main_item['body'].setdefault('residential_address', []).append(local_addr)
            for entry in address_data['entries']:
                if entry['level'] == '4':
                    local_addr['KLADR_locality'] = entry['kladrCode']
                elif entry['level'] == '5':
                    local_addr['KLADR_street'] = entry['kladrCode']

        # schema = {
        #     "blood_type_info": {  # добавят в patients-smart-ws позже
        #         "type": "array",
        #         "description": "Данные группы крови и резус-фактора пациентки",
        #         "items": {
        #             "type": "object",
        #             "description": "Сведение о группе крови и резус-факторе",
        #             "properties": {
        #
        #                 "blood_type": {
        #                     "type": "string",
        #                     "description": "Код группы крови",
        #                     "enum":
        #                         [
        #                             "0(I)Rh-",
        #                             "0(I)Rh+",
        #                             "A(II)Rh-",
        #                             "A(II)Rh+",
        #                             "B(III)Rh-",
        #                             "B(III)Rh+",
        #                             "AB(IV)Rh-",
        #                             "AB(IV)Rh+",
        #                             "0(I)RhDu",
        #                             "A(II)RhDu",
        #                             "B(III)RhDu",
        #                             "AB(IV)RhDu"
        #                         ]
        #                 }
        #             },
        #             "required": [
        #                 "blood_type"
        #             ]
        #         }
        #     },
        #     "allergies_info": {  # в мис вроде нет инфы такой
        #     },
        #     "medicine_intolerance_info": {  # в мис вроде нет инфы такой
        #     }
        # }

        return res

    ##################################################################
    ##  reform requests

    def get_remote_request(self, header_meta):
        local_entity_code = header_meta['local_entity_code']
        if local_entity_code == LocalEntityCode.CLIENT:
            req_data = self.build_remote_patient_request(header_meta)
            self.set_remote_id(req_data)
            self.set_remote_service_request(req_data)
        else:
            raise RuntimeError('Unexpected local_entity_code')
        return req_data

    def build_remote_patient_request(self, header_meta):
        req_data = {
            'meta': {
                'src_entity_code': header_meta['local_entity_code'],
                'src_id': header_meta['local_main_id'],
                'dst_system_code': self.remote_sys_code,
                'dst_entity_code': RemoteEntityCode.PATIENT,
                'dst_operation_code': header_meta['local_operation_code'],
                'dst_id': None,
            }
        }
        return req_data

    def set_remote_id(self, req_data):
        req_meta = req_data['meta']
        if req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            matching_id_data = MatchingId.first_remote_id(
                req_meta['src_entity_code'],
                req_meta['src_id'],
                req_meta['dst_entity_code'],
                self.remote_sys_code,
            )
            if matching_id_data:
                req_meta['dst_id'] = matching_id_data['dst_id']
                req_meta['dst_id_url_param_name'] = matching_id_data['dst_id_url_param_name']
            else:
                raise ApiException(400, 'This entity has not yet passed')

    def set_remote_service_request(self, req_data):
        req_meta = req_data['meta']
        method = ApiMethod.get_method(
            req_meta['dst_entity_code'],
            req_meta['dst_operation_code'],
            self.remote_sys_code,
        )
        req_meta.update({
            'dst_protocol_code': method['protocol'],
            'dst_method': method['method'],
            'dst_url': method['template_url'],
        })
        if method['protocol'] == ProtocolCode.REST:
            if req_meta['dst_operation_code'] != OperationCode.READ_ALL:
                req_meta['dst_url'] = req_meta['dst_url'].replace(
                    req_meta['dst_id_url_param_name'].join(('<int:', '>')),
                    str(req_meta['dst_id'])
                )

    ##################################################################
    ##  build packages

    ##################################################################
    ##  build packages patient

    def get_entity_packages(self, reformed_req):
        """
        Args:
            reformed_req: данные для запроса корневой сущности

        Returns: мета данные и пакеты сущностей

        Сбор сущностей в пакеты дозапросами.
        root_parent проставляется только для узла, у которого есть childs, но
        сам этот узел не корневой.
        is_changed - признак изменения пакета сущностей. ставится дефолт True

        entity_packages = {
            RemoteEntityCode.PATIENT: [
                {  # -> patient_node
                    'is_changed': True,
                    'main_id': patient_uid,
                    'data': {...},
                    'childs': {
                        RemoteEntityCode.IND_ADDRESS: [
                            {
                                'root_parent': patient_node,
                                'data': {...},
                                'childs': {
                                    EntityCode...
                                },
                            }
                        ],
                        RemoteEntityCode.IND_DOCUMENTS: [
                            {
                                'data': {...},
                            }
                        ],
                    },
                },
            ]
        }
        """
        # todo: вынести в ApiMethod метод, url дозапросов и возможно доступ к параметрам,
        # todo: когда станет ясно как их лучше хранить
        # todo: рассмотреть возможность использования MatchingEntity для автосборки пакетов
        # todo: дозапросы будут переделаны в соответствии с новой wsdl
        entity_packages = {}
        meta = reformed_req['meta']
        dst_entity = meta['dst_entity_code']
        dst_url = meta['dst_url']
        # remote_entities = MatchingEntity.get_remote(
        #     src_entity, self.remote_sys_code
        # )
        # missing_entities = remote_entities - {dst_entity}
        if dst_entity == RemoteEntityCode.PATIENT:
            req = reformed_req
            fl_data_url = 'http://develop.r-mis.ru/individuals-ws/individuals?wsdl'
            patients_list = self.transfer__send_request(req)
            if meta['dst_operation_code'] == OperationCode.READ_ALL:
                for patient_item in patients_list:
                    patient_uid = patient_item.uid
                    root_parent = patient_node = {
                        'is_changed': True,
                        'main_id': patient_item.id,
                        'data': patient_item,
                    }
                    entity_packages.setdefault(
                        RemoteEntityCode.PATIENT, []
                    ).append(patient_node)
                    # req = {
                    #     'meta': {
                    #         'dst_method': 'getPatient',
                    #         'dst_url': dst_url,
                    #         'dst_id_url_param_name': 'uid',
                    #         'dst_id': patient_item,
                    #     },
                    # }
                    # patient_data = self.transfer_give_data(req)

                    req = {
                        'meta': {
                            'dst_method': 'getIndividualAddresses',
                            'dst_url': fl_data_url,
                            'dst_id_url_param_name': 'uid',
                            'dst_id': patient_uid,
                        },
                    }
                    patient_childs = patient_node.setdefault('childs', {})
                    if patient_node != root_parent:
                        patient_node['root_parent'] = root_parent
                    IndividualAddresses_list = self.transfer__send_request(req)
                    for ind_addr_item in IndividualAddresses_list:
                        ind_address_node = {'data': ind_addr_item}
                        patient_childs.setdefault(
                            RemoteEntityCode.IND_ADDRESS, []
                        ).append(ind_address_node)
                        # req = {
                        #     'meta': {
                        #         'dst_method': 'getAddressAllInfo',
                        #         'dst_url': fl_data_url,
                        #         'dst_id_url_param_name': 'uid',
                        #         'dst_id': ind_addr_item,
                        #     },
                        # }
                        # AddressAllInfo_data = self.transfer_give_data(req)

                    req = {
                        'meta': {
                            'dst_method': 'getIndividualDocuments',
                            'dst_url': fl_data_url,
                            'dst_id_url_param_name': 'uid',
                            'dst_id': patient_uid,
                        },
                    }
                    IndividualDocuments_list = self.transfer__send_request(req)
                    for ind_doc_item in IndividualDocuments_list:
                        ind_documents_data = {'data': ind_doc_item}
                        patient_childs.setdefault(
                            RemoteEntityCode.IND_DOCUMENTS, []
                        ).append(ind_documents_data)
                        # req = {
                        #     'meta': {
                        #         'dst_method': 'getDocument',
                        #         'dst_url': fl_data_url,
                        #         'dst_id_url_param_name': 'uid',
                        #         'dst_id': ind_doc_item,
                        #     },
                        # }
                        # Document_data = self.transfer_give_data(req)
        return meta, entity_packages

    def create_remote_messages(self, entity_packages):
        meta, packages = entity_packages
        dst_entity_code = meta['dst_entity_code']
        for item in packages[dst_entity_code]:
            if not item['is_changed']:
                continue
            msg = Message(item)
            msg.to_local_service()
            msg.set_send_data_type()
            header_meta = msg.get_header().meta
            header_meta.update({
                'remote_system_code': self.remote_sys_code,
                # 'remote_operation_code': OperationCode.CHANGE,
                'remote_entity_code': dst_entity_code,
                'remote_main_id': meta['dst_id'],
                'remote_method': meta['dst_method'],
            })
