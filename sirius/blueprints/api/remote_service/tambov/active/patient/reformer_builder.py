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
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.method import ApiMethod
from sirius.lib.xform import Undefined
from sirius.models.system import SystemCode
from sirius.models.operation import OperationCode

encode = WebMisJsonEncoder().default


class PatientTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  reform requests

    def build_remote_request(self, header_meta, dst_entity_code):
        req_data = self.build_remote_request_common(header_meta, dst_entity_code)
        return req_data


    ##################################################################
    ##  build packages by req

    def build_remote_entity_packages(self, reformed_req):
        package = EntitiesPackage(self, self.remote_sys_code)
        req_meta = reformed_req.meta
        if req_meta['dst_operation_code'] == OperationCode.READ_MANY:
            api_method = self.reformer.get_api_method(
                self.remote_sys_code,
                TambovEntityCode.PATIENT,
                OperationCode.READ_ONE,
            )
            all_patients = self.get_all_patients(reformed_req)
            changed_patients = self.get_changed_patients(reformed_req)
            self.set_patient_cards(changed_patients, package, api_method, req_meta)
            self.inject_all_patients(package, all_patients, api_method)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            api_method = self.reformer.get_api_method(
                self.remote_sys_code,
                TambovEntityCode.PATIENT,
                OperationCode.READ_ONE,
            )
            self.set_patient_cards([req_meta['dst_id']], package, api_method, req_meta)
        return package

    def get_all_patients(self, reformed_req):
        req = reformed_req.copy()
        patients_uids = set()
        res = None
        page = 1
        while res or page == 1:
            req.data_update({'page': page, 'gender': 2})
            res = self.transfer__send_request(req)
            patients_uids.update(res)
            page += 1
            # for test just 2 pages
            if page > 1:
                break
        return patients_uids

    def get_changed_patients(self, reformed_req):
        req = reformed_req.copy()
        patient_uids = []
        res = None
        page = 1
        # todo: брать из даты начала работы планировщика по сущности
        modified_since = date(2016, 11, 1)
        while res or page == 1:
            req.data_update({
                'page': page,
                'gender': 2,
                'modifiedSince': modified_since,
            })
            res = self.transfer__send_request(req)
            patient_uids.extend(res)
            page += 1
            # for test just 2 pages
            if page > 1:
                break
        return patient_uids

    def inject_all_patients(self, package, all_patients, api_method):
        # Добавляемые uid нужны будут для определения удаленных пациентов
        nodes = package.get_entities(TambovEntityCode.PATIENT)
        for patient_node in nodes:
            if patient_node['main_id'] in all_patients:
                all_patients.remove(patient_node['main_id'])
        for pat_uid in all_patients:
            package.add_main_pack_entity(
                entity_code=TambovEntityCode.PATIENT,
                method=api_method['method'],
                main_param_name='patientUid',
                main_id=pat_uid,
                parents_params=None,
                data=None,
            )

    def set_patient_cards(self, changed_patients, package, api_method, req_meta):
        for patient_uid in changed_patients:
            # отброс мусора с тестовой БД
            if not patient_uid:
                continue
            req = DataRequest()
            req.set_req_params(
                url=api_method['template_url'],
                method=api_method['method'],
                data={'patientUid': patient_uid},
            )
            patient_data = self.transfer__send_request(req)
            main_item = package.add_main_pack_entity(
                entity_code=TambovEntityCode.PATIENT,
                method=req.method,
                main_param_name='patientUid',
                main_id=patient_uid,
                parents_params=req_meta['dst_parents_params'],
                data=patient_data,
            )

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

    ##################################################################
    ##  reform entities

    def build_local_entities(self, header_meta, pack_entity):
        patient_data = pack_entity['data']
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = header_meta['remote_operation_code']

        # сопоставление параметров родительских сущностей
        # params_map = {
        #     TambovEntityCode.PATIENT: {
        #         'entity': RisarEntityCode.CARD, 'param': 'card_id'
        #     }
        # }
        # self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        main_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.CLIENT,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='client_id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            self.build_local_client_body(main_item, patient_data)

        return entities

    def build_local_client_body(self, main_item, patient_data):
        patient = patient_data['patient']
        gender = safe_int(patient.gender)
        # if gender != 2:
        #     main_item['meta']['skip_trash'] = True
        main_item['body'] = {
            # 'client_id': None,  # заполняется в set_current_id_func
            'FIO': {
                'middlename': patient['middleName'],
                'name': patient['firstName'],
                'surname': patient['lastName']
            },
            'birthday_date': encode(patient['birthDate']),
            'gender': gender,
            # 'SNILS': None,  # заполняется в документах
            'blood_type_info': {
                'blood_type': patient.get('bloodGroup', ''),
            },
        }
        for document_data in patient_data.identifiers:
            if not document_data.type:
                continue
            if document_data.type == '19':  # SNILS
                main_item['body']['SNILS'] = document_data.number
            # elif document_data.codeType == '1' and not main_item['body']['SNILS'] is None:  # SNILS
            #     main_item['body']['SNILS'] = document_data.code
            elif document_data.type == '26':  # ENP
                main_item['body'].setdefault('insurance_documents', []).append({
                    # todo: синхронизация справочников
                    'insurance_document_type': document_data.type or '',
                    'insurance_document_number': document_data.number or '',
                    'insurance_document_beg_date': encode(document_data.issueDate) or '',
                    'insurance_document_series': document_data.series or Undefined,
                    # todo: error: has no method get
                    # 'document_issuing_authority': safe_traverse(document_data, 'issueOrganization', 'code'),
                    # todo: синхронизация справочников
                    # 'insurance_document_issuing_authority': document_data.issueOrganization and document_data.issueOrganization.code or '',
                    'insurance_document_issuing_authority': '64014',    # —
                })
            elif document_data.type == '13':  # passport
                # todo: в схеме рисар document будет переделан на список documents. зачем?
                main_item['body'].setdefault('document', {}).update({
                    # todo: синхронизация справочников
                    'document_type_code': safe_int(document_data.type),
                    'document_number': document_data.number,
                    'document_beg_date': encode(document_data.issueDate) or '',
                    'document_series': document_data.series or Undefined,
                    # todo: error: has no method get
                    # 'document_issuing_authority': safe_traverse(document_data, 'issueOrganization', 'code'),
                    'document_issuing_authority': document_data.issueOrganization and document_data.issueOrganization.code or Undefined,
                })
            else:
                pass
        # Женя: Берем только один адрес проживания, всё остальное пофиг. Если их несколько - берем первый
        for address_data in patient_data['addresses']:
            local_addr = {
                'KLADR_locality': None,  # заполняется в entry
                'KLADR_street': None,  # заполняется в entry
                'house': address_data['house'],  # заполняется в entry
                'locality_type': None,  # заполняется в entry
                # todo:
                # 'building': 'not-implemented' or Undefined,
                'flat': address_data['apartment'] or Undefined,
            }
            # в схеме рисар пока не массив, а объект
            # main_item['body'].setdefault('residential_address', []).append(local_addr)
            main_item['body']['residential_address'] = local_addr
            local_addr['locality_type'] = 1     # —
            for entry in address_data['entries']:
                if entry['level'] == '5':
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

        #######################
        ## RisarEntityCode.CARD

        # def set_current_id_func(record):
        #     reform_meta = record['meta']
        #     record['body'].update({
        #         'client_id': reform_meta['dst_id'],
        #     })
        # main_item = self.set_main_entity(
        #     node=res,
        #     dst_entity_code=RisarEntityCode.CARD,
        #     dst_parents_params=header_meta['local_parents_params'],
        #     src_operation_code=header_meta['remote_operation_code'],
        #     src_entity_code=src_entity_code,
        #     src_id_url_param_name=header_meta['remote_main_param_name'],
        #     src_id=header_meta['remote_main_id'],
        #     level=1,
        #     level_count=1,
        #     set_current_id_func=set_current_id_func,
        # )
        # main_item['body'] = {
        #     'client_id': None,  # заполняется в set_current_id_func
        #     'card_set_date': encode(date.today()),
        #     'card_doctor': '-1',
        #     'card_LPU': '-1',
        # }

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

        # todo: дозапросы будут переделаны в соответствии с новой wsdl
        # todo: ждем доработку wsdl по группе крови
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
