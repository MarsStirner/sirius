#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date

from hitsl_utils.safe import safe_traverse, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.reformer.api import Builder
from sirius.blueprints.reformer.models.method import ApiMethod
from sirius.lib.remote_system import RemoteSystemCode
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode


class PatientTambovBuilder(Builder):
    remote_sys_code = RemoteSystemCode.TAMBOV

    ##################################################################
    ##  reform entities client

    def build_local_client(self, header_meta, entity_package, addition_data):
        patient_data = entity_package['data']
        src_entity_code = header_meta['remote_entity_code']

        def set_current_id_func(record):
            reform_meta = record['meta']
            record['body'].update({
                'client_id': reform_meta['dst_id'] or Undefined,
            })
        res = {
            'operation_order': {},
            RisarEntityCode.CLIENT: [{
                'meta': {
                    'src_entity_code': src_entity_code,
                    'src_id': header_meta['remote_main_id'],
                    'dst_entity_code': RisarEntityCode.CLIENT,
                    'set_current_id_func': set_current_id_func,
                    'src_operation_code': header_meta['remote_operation_code'],
                },
            }],
        }
        main_item = res[RisarEntityCode.CLIENT][0]
        self.set_operation_order(res, RisarEntityCode.CLIENT, 1)
        patient = patient_data['patient']
        gender = safe_int(patient.gender)
        # if gender != 2:
        #     main_item['meta']['skip_trash'] = True
        main_item['body'] = {
            'client_id': None or Undefined,  # заполняется в set_current_id_func
            'FIO': {
                'middlename': patient['middleName'],
                'name': patient['firstName'],
                'surname': patient['lastName']
            },
            'birthday_date': WebMisJsonEncoder().default(patient['birthDate']),
            'gender': gender,
            'SNILS': None or Undefined,  # заполняется в документах
        }
        for document_data in patient_data.identifiers:
            if document_data.type == '19':  # SNILS
                main_item['body']['SNILS'] = document_data.code
            else:
                # todo: в схеме рисар document будет переделан на список documents
                main_item['body'].setdefault('documents', []).append({
                    'document_type_code': safe_int(document_data.type),
                    'document_number': document_data.number,
                    'document_beg_date': document_data.activationDate,
                    'document_series': document_data.series or Undefined,
                    # todo: error: has no method get
                    # 'document_issuing_authority': safe_traverse(document_data, 'issueOrganization', 'name'),
                    'document_issuing_authority': document_data.issueOrganization and document_data.issueOrganization.name or Undefined,
                })
        # Женя: Берем только один адрес проживания, всё остальное пофиг. Если их несколько - берем первый
        for address_data in patient_data['addresses']:
            local_addr = {
                'KLADR_locality': None,  # заполняется в entry
                'KLADR_street': None,  # заполняется в entry
                'house': address_data['house'],  # заполняется в entry
                'locality_type': None,  # заполняется в entry
                # todo:
                'building': 'not-implemented' or Undefined,
                'flat': address_data['apartment'] or Undefined,
            }
            # в схеме рисар пока не массив, а объект
            # main_item['body'].setdefault('residential_address', []).append(local_addr)
            main_item['body']['residential_address'] = local_addr
            local_addr['locality_type'] = 1
            for entry in address_data['entries']:
                if entry['level'] == '4':
                    local_addr['KLADR_locality'] = entry['kladrCode'][:11] + '00'
                    # local_addr['locality_type'] = '1' if entry['type'] == '18' else '2'
                elif entry['level'] == '6':
                    local_addr['KLADR_street'] = entry['kladrCode']
                elif entry['level'] == '7':
                    local_addr['house'] = entry['name']
                elif entry['level'] == '8':
                    local_addr['flat'] = entry['name']
            # в схеме рисар пока не массив, а объект
            break

        # образец работы с дозапросами
        # childs = entity_package['childs']
        # document_list = childs[TambovEntityCode.IND_DOCUMENTS]
        # for item in document_list:
        #     document_data = item['data']
        #     if document_data['type'] == '19':  # SNILS
        #         main_item['body']['SNILS'] = document_data['code']
        #     else:
        #         # todo: в схеме рисар document будет переделан на список documents
        #         main_item['body'].setdefault('documents', []).append({
        #             'document_type_code': document_data['type'],
        #             'document_number': document_data['number'],
        #             'document_beg_date': document_data['activationDate'],
        #             # необязательные
        #             'document_series': document_data['series'],
        #             'document_issuing_authority': document_data['issueOrganization'],
        #         })
        #
        # address_list = childs[TambovEntityCode.IND_ADDRESS]
        # for item in address_list:
        #     address_data = item['data']
        #     local_addr = {
        #         'KLADR_locality': None,  # заполняется в entry
        #         'KLADR_street': None,  # заполняется в entry
        #         'house': address_data['house'],
        #         'locality_type': address_data[''],
        #         # необязательные
        #         'building': address_data[''],
        #         'flat': address_data['apartment'],
        #     }
        #     main_item['body'].setdefault('residential_address', []).append(local_addr)
        #     for entry in address_data['entries']:
        #         if entry['level'] == '4':
        #             local_addr['KLADR_locality'] = entry['kladrCode']
        #         elif entry['level'] == '5':
        #             local_addr['KLADR_street'] = entry['kladrCode']

        # ждем доработку wsdl по группе крови
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
    ##  reform patient requests

    def build_remote_patient_request(self, header_meta):
        req_data = {
            'meta': {
                'src_entity_code': header_meta['local_entity_code'],
                'src_id': header_meta['local_main_id'],
                'dst_system_code': self.remote_sys_code,
                'dst_entity_code': TambovEntityCode.PATIENT,
                'dst_operation_code': header_meta['local_operation_code'],
                'dst_id': None,
            }
        }
        return req_data

    ##################################################################
    ##  build packages patient

    def build_remote_patient_entity_packages(self, reformed_req):
        entities = {}
        entity_packages = {
            'system_code': self.remote_sys_code,
            'entities': entities,
        }
        req_meta = reformed_req['meta']
        if req_meta['dst_operation_code'] == OperationCode.READ_ALL:
            api_method = ApiMethod.get_method(
                TambovEntityCode.PATIENT,
                OperationCode.READ_ONE,
                self.remote_sys_code,
            )
            all_patients = self.get_all_patients(reformed_req)
            changed_patients = self.get_changed_patients(reformed_req)
            self.set_patient_cards(changed_patients, entities, api_method)
            self.inject_all_patients(entities, all_patients, api_method)
        return entity_packages

    def get_all_patients(self, reformed_req):
        req = reformed_req.copy()
        patients_uids = set()
        res = None
        page = 1
        while res or page == 1:
            req['meta'].update({
                'dst_id_url_param_name': ['page', 'gender'],
                'dst_id': [page, 2],
            })
            res = self.transfer__send_request(req)
            patients_uids.update(res)
            page += 1
            # for test just 2 pages
            if page > 2:
                break
        return patients_uids

    def get_changed_patients(self, reformed_req):
        req = reformed_req.copy()
        patient_uids = []
        res = None
        page = 1
        modified_since = date(2016, 9, 1)
        while res or page == 1:
            req['meta'].update({
                'dst_id_url_param_name': ['page', 'gender', 'modifiedSince'],
                'dst_id': [page, 2, modified_since],
            })
            res = self.transfer__send_request(req)
            patient_uids.extend(res)
            page += 1
            # for test just 2 pages
            if page > 2:
                break
        return patient_uids

    def inject_all_patients(self, entities, all_patients, api_method):
        # Добавляемые uid нужны будут для определения удаленных пациентов
        nodes = entities[TambovEntityCode.PATIENT]
        for patient_node in nodes:
            if patient_node['main_id'] in all_patients:
                all_patients.remove(patient_node['main_id'])
        for pat_uid in all_patients:
            patient_node = {
                'is_changed': False,
                'method': api_method['method'],
                'main_id': pat_uid,
                'data': None,
            }
            nodes.append(patient_node)

    def set_patient_cards(self, changed_patients, entities, api_method):
        for patient_uid in changed_patients:
            # отброс мусора с тестовой БД
            if not patient_uid:
                continue
            req = {
                'meta': {
                    'dst_method': api_method['method'],
                    'dst_url': api_method['template_url'],
                    'dst_id_url_param_name': 'patientUid',
                    'dst_id': patient_uid,
                },
            }
            patient_data = self.transfer__send_request(req)
            root_parent = patient_node = {
                'is_changed': False,
                'method': req['meta']['dst_method'],
                'main_id': patient_uid,
                'data': patient_data,
            }
            entities.setdefault(
                TambovEntityCode.PATIENT, []
            ).append(patient_node)

            # образец работы с дозапросами
            # individuals_url = 'http://develop.r-mis.ru/individuals-ws/individuals?wsdl'
            # req = {
            #     'meta': {
            #         'dst_method': 'getIndividualAddresses',
            #         'dst_url': individuals_url,
            #         'dst_id_url_param_name': 'uid',
            #         'dst_id': patient_uid,
            #     },
            # }
            # patient_childs = patient_node.setdefault('childs', {})
            # if patient_node != root_parent:
            #     patient_node['root_parent'] = root_parent
            # IndividualAddresses_list = self.transfer__send_request(req)
            # for ind_addr_item in IndividualAddresses_list:
            #     ind_address_node = {'data': ind_addr_item, 'main_id': ind_addr_item.id}
            #     patient_childs.setdefault(
            #         TambovEntityCode.IND_ADDRESS, []
            #     ).append(ind_address_node)
            #     # req = {
            #     #     'meta': {
            #     #         'dst_method': 'getAddressAllInfo',
            #     #         'dst_url': fl_data_url,
            #     #         'dst_id_url_param_name': 'uid',
            #     #         'dst_id': ind_addr_item,
            #     #     },
            #     # }
            #     # AddressAllInfo_data = self.transfer__send_request(req)
            #
            # req = {
            #     'meta': {
            #         'dst_method': 'getIndividualDocuments',
            #         'dst_url': individuals_url,
            #         'dst_id_url_param_name': 'uid',
            #         'dst_id': patient_uid,
            #     },
            # }
            # IndividualDocuments_list = self.transfer__send_request(req)
            # for ind_doc_item in IndividualDocuments_list:
            #     ind_documents_data = {'data': ind_doc_item, 'main_id': ind_doc_item.id}
            #     patient_childs.setdefault(
            #         TambovEntityCode.IND_DOCUMENTS, []
            #     ).append(ind_documents_data)
            #     # req = {
            #     #     'meta': {
            #     #         'dst_method': 'getDocument',
            #     #         'dst_url': fl_data_url,
            #     #         'dst_id_url_param_name': 'uid',
            #     #         'dst_id': ind_doc_item,
            #     #     },
            #     # }
            #     # Document_data = self.transfer__send_request(req)
