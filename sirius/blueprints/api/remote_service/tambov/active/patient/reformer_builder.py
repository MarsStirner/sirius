#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date

from hitsl_utils.safe import safe_traverse_attrs, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.method import ApiMethod
from sirius.blueprints.scheduler.models import SchGrReqExecute
from sirius.lib.xform import Undefined
from sirius.models.system import SystemCode
from sirius.models.operation import OperationCode

encode = lambda x: x and WebMisJsonEncoder().default(x)


class PatientTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  reform requests

    def build_remote_request(self, header_meta, dst_entity_code):
        req_data = self.build_remote_request_common(header_meta, dst_entity_code)
        return req_data


    ##################################################################
    ##  build remote packages by req

    def build_remote_entity_packages(self, reformed_req):
        package = EntitiesPackage(self, self.remote_sys_code)
        req_meta = reformed_req.meta
        if req_meta['dst_operation_code'] == OperationCode.READ_MANY:
            # проблема с определением ключа выборки
            # package.enable_diff_check()
            api_method = self.reformer.get_api_method(
                self.remote_sys_code,
                TambovEntityCode.SMART_PATIENT,
                OperationCode.READ_ONE,
            )
            all_patients = self.get_all_patients(reformed_req)
            changed_patients = self.get_changed_patients(reformed_req, package)
            # changed_patients = ['1054287']  # for test
            self.set_patient_cards(changed_patients, package, req_meta)
            self.inject_all_patients(package, all_patients, api_method)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            self.set_patient_cards([req_meta['dst_id']], package, req_meta)
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

    def get_changed_patients(self, reformed_req, package):
        req = reformed_req.copy()
        patient_uids = []
        res = None
        page = 1
        # todo: включить после тестов
        # last_exec_datetime = SchGrReqExecute.last_datetime(RisarEntityCode.CLIENT) or datetime.today()
        # modified_since = last_execute_datetime.date()
        modified_since = date(2016, 11, 1)
        # package.set_diff_key_range((modified_since.isoformat(),
        #                             date.today().isoformat()))
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
        nodes = package.get_entities(TambovEntityCode.SMART_PATIENT)
        for patient_node in nodes:
            if patient_node['main_id'] in all_patients:
                all_patients.remove(patient_node['main_id'])
        for pat_uid in all_patients:
            package.add_main_pack_entity(
                entity_code=TambovEntityCode.SMART_PATIENT,
                method=api_method['method'],
                main_param_name='patientUid',
                main_id=pat_uid,
                parents_params=None,
                data=None,
            )

    def set_patient_cards(self, changed_patients, package, req_meta):
        for patient_uid in changed_patients:
            # отброс мусора с тестовой БД
            if not patient_uid:
                continue
            main_item, _ = package.add_main(
                entity_code=TambovEntityCode.SMART_PATIENT,
                main_id_name='patientUid',
                main_id=patient_uid,
                parents_params=req_meta['dst_parents_params'],
                # diff_key=,
            )
            package.add_addition(
                parent_item=main_item,
                entity_code=TambovEntityCode.PATIENT,
                main_id_name=None,
                main_id=patient_uid,
            )

    ##################################################################
    ##  reform entities

    def build_local_entities(self, header_meta, pack_entity):
        sm_patient_data = pack_entity['data']
        patient_node = pack_entity['addition'][TambovEntityCode.PATIENT][0]
        patient_data = patient_node['data']
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = header_meta['remote_operation_code']

        # сопоставление параметров родительских сущностей
        # params_map = {
        #     TambovEntityCode.SMART_PATIENT: {
        #         'entity': RisarEntityCode.CARD, 'param': 'card_id'
        #     }
        # }
        # self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities(self.reformer.stream_id)
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
            self.build_local_client_body(main_item, sm_patient_data, patient_data)

        return entities

    def build_local_client_body(self, main_item, sm_patient_data, patient_data):
        patient = sm_patient_data['patient']
        gender = safe_int(patient.gender)
        # if gender != 2:
        #     main_item['meta']['skip_trash'] = True
        main_item['body'] = {
            # 'client_id': None,  # заполняется в set_current_id_func
            'FIO': {
                'middlename': patient['middleName'] or '',
                'name': patient['firstName'],
                'surname': patient['lastName']
            },
            'birthday_date': encode(patient['birthDate']),
            'gender': gender,
            # 'SNILS': None,  # заполняется в документах
        }
        if sm_patient_data['workplaces']:
            workplace = sm_patient_data['workplaces'][-1]
            main_item['body']['job'] = {
                'organisation': workplace['organization']['name'],
                'post': workplace['position'] or Undefined,
            }
        if patient_data['bloodGroup']:
            main_item['body']['blood_type_info'] = [{
                'blood_type': patient_data['bloodGroup'],
            }]
        for document_data in sm_patient_data.identifiers:
            if not document_data.type:
                continue

            # Получаем код организации
            document_issuing_authority = Undefined
            for code in (safe_traverse_attrs(document_data, 'issueOrganization', 'codes') or {}):
                if code['type'] == 'CODE_OMS':
                    document_issuing_authority = code['code']
                    break
            if document_data.type == '19':  # SNILS
                main_item['body']['SNILS'] = document_data.number
            # elif document_data.codeType == '1' and not main_item['body']['SNILS'] is None:  # SNILS
            #     main_item['body']['SNILS'] = document_data.code
            elif document_data.type in ('24', '25', '26', '40'):  # ENP
                # в insurance_document_issuing_authority приходит код, а нужно ИД
                continue
                main_item['body'].setdefault('insurance_documents', []).append({
                    'insurance_document_type': document_data.type or '',
                    'insurance_document_number': document_data.number or '',
                    'insurance_document_beg_date': encode(document_data.issueDate) or '',
                    'insurance_document_series': document_data.series or Undefined,
                    'insurance_document_issuing_authority': document_issuing_authority,    # —
                })
            else:  # passport ('13') и прочие документы
                main_item['body'].setdefault('documents', []).append({
                    'document_type_code': safe_int(document_data.type),
                    'document_number': document_data.number,
                    'document_beg_date': encode(document_data.issueDate) or '2000-01-01',
                    'document_series': document_data.series or Undefined,
                    'document_issuing_authority': document_issuing_authority,
                })
        for address_data in sm_patient_data['addresses']:
            if address_data['type'] == '3':
                addr_type_name = 'residential_address'
            elif address_data['type'] == '4':
                addr_type_name = 'registration_address'
            else:
                continue
            # дефолты. заполняется в entry
            local_addr = {
                'KLADR_locality': '',
                'KLADR_street': '',
                'house': address_data['house'] or '0',
                'locality_type': 1,
                # Женя: building не передаем. они корпус пишут в номер дома
                # 'building': 'not-implemented' or Undefined,
                'flat': address_data['apartment'] or '0',
            }
            main_item['body'][addr_type_name] = local_addr
            for entry in sorted(address_data['entries'], key=lambda x: x['level'], reverse=True):
                if entry['level'] == '2':
                    if not local_addr['KLADR_locality']:
                        local_addr['KLADR_locality'] = entry['kladrCode'][:11] + '00'
                elif entry['level'] == '4':
                    if not local_addr['KLADR_locality']:
                        local_addr['KLADR_locality'] = entry['kladrCode'][:11] + '00'
                elif entry['level'] == '5':
                    local_addr['KLADR_locality'] = entry['kladrCode'][:11] + '00'
                elif entry['level'] == '6':
                    local_addr['KLADR_street'] = entry['kladrCode'] or ''
                elif entry['level'] == '7' and entry['name']:
                    local_addr['house'] = entry['name']
                elif entry['level'] == '8' and entry['name']:
                    local_addr['flat'] = entry['name']

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
