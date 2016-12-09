#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime

from hitsl_utils.safe import safe_traverse, safe_int, safe_traverse_attrs, \
    safe_bool_none, safe_double, safe_bool
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.blueprints.reformer.models.method import ApiMethod
from sirius.models.system import SystemCode
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode

encode = lambda x: x is not None and WebMisJsonEncoder().default(x)
to_date = lambda x: datetime.strptime(x, '%Y-%m-%d')


class BirthTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  reform requests

    def build_remote_request(self, header_meta, dst_entity_code):
        # сопоставление параметров родительских сущностей
        src_entity_code = header_meta['local_entity_code']
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TambovEntityCode.SMART_PATIENT, 'param': 'patient_id'  # !!!
            },
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)
        # todo для отладки по стенду
        # header_meta['remote_parents_params']['patient_id']['id'] = '1342306'

        req_data = self.build_remote_request_common(header_meta, dst_entity_code)
        return req_data

    ##################################################################
    ##  build packages

    def build_remote_entity_packages(self, reformed_req):
        package = EntitiesPackage(self, self.remote_sys_code)
        req_meta = reformed_req.meta

        for param_name, param_data in reformed_req.meta['dst_parents_params'].items():
            reformed_req.data_update({param_name: param_data['id']})
        birth_data = self.transfer__send_request(reformed_req)
        main_item = package.add_main_pack_entity(
            entity_code=TambovEntityCode.BIRTH,
            method=reformed_req.method,
            main_param_name='PatientId',
            main_id=birth_data['PatientId'],
            parents_params=req_meta['dst_parents_params'],
            data=birth_data,
            is_changed=True,  # см. todo в difference
        )
        return package

    ##################################################################
    ##  reform entities

    def build_local_entities(self, header_meta, pack_entity):
        birth_data = pack_entity['data']
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = header_meta['remote_operation_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            TambovEntityCode.SMART_PATIENT: {
                'entity': RisarEntityCode.CARD, 'param': 'card_id'
            },
        }
        self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        if not safe_traverse_attrs(birth_data, 'Part1', 'InDate'):
            # пустой ответ
            return entities
        main_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.CHILDBIRTH,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='card_id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            sta = safe_traverse_attrs
            part1 = birth_data['Part1']
            part2 = birth_data['Part2']
            part3 = birth_data['Part3']
            part4 = birth_data['Part4']
            part5 = birth_data['Part5']
            part6 = birth_data['Part6']
            # days = safe_int(sta(part1, 'PregnantTimeSpan', 'Days'))
            main_item['body'] = {
                # "required": ["admission_date", "pregnancy_duration",
                #              "delivery_date", "delivery_time",
                #              "maternity_hospital", "diagnosis_osn",
                #              "pregnancy_final"]
                'general_info': {
                    'admission_date': encode(part1['InDate']),
                    'maternity_hospital': str(sta(part1, 'ClinicId')),
                    'delivery_date': encode(sta(part1, 'ChildBirth', 'Date')),
                    'delivery_time': encode(sta(part1, 'ChildBirth', 'Time'))[:5],

                    # todo: test
                    # 'pregnancy_final': sta(part1, 'ChildBirth', 'ChildBirthOutcome'),  # rbRisarPregnancy_Final
                    'pregnancy_final': 'rodami',  # rbRisarPregnancy_Final

                    'pregnancy_duration': sta(part1, 'ChildBirth', 'PregnantWeeks'),
                    # 'pregnancy_duration': days and int(days / 7) or 0,
                    'diagnosis_osn': sta(part1, 'ChildBirth', 'Diagnoses', 'MainDiagnos'),
                    # --
                    # 'diagnosis_sop': part1['Extra'] or Undefined,
                    # 'diagnosis_osl': part1['Complication'] or Undefined,
                    'maternity_hospital_doctor': (lambda x: x and str(x) or Undefined)(sta(part1, 'ChildBirth', 'EmployeeId')),
                    'curation_hospital': sta(part1, 'CuratioLpu') or Undefined,
                    'pregnancy_speciality': sta(part1, 'BirthSpeciality') or Undefined,
                    'postnatal_speciality': sta(part1, 'AfterBirthSpeciality') or Undefined,
                    'help': sta(part1, 'HelpProvided') or Undefined,
                    # 'abortion': sta(part1, 'Abort') or Undefined,  # rbRisarAbort
                    # 'death': ???,
                },
                'complications': {
                    # 'delivery_waters': part3['BirthWaterBreak'] or Undefined,  # rbRisarDelivery_Waters
                    'pre_birth_delivery_waters': safe_bool_none(part3['PrenatalWaterBreak']) or Undefined,
                    'weakness': sta(part3, 'BirthPowerWeakness') or Undefined,  # rbRisarWeakness
                    'meconium_color': safe_bool_none(sta(part3, 'AmiaticWater')) or Undefined,
                    'pathological_preliminary_period': safe_bool_none(sta(part3, 'PatologicPreliminaryPeriod')) or Undefined,
                    'abnormalities_of_labor': safe_bool_none(sta(part3, 'BirthActivityAnomaly')) or Undefined,
                    'chorioamnionitis': safe_bool_none(sta(part3, 'Horiamnionit')) or Undefined,
                    # 'perineal_tear': part3['PerinealRupture'] or Undefined,  # rbPerinealTear
                    # 'eclampsia': part3['Nefropaty'] or Undefined,  # rbRisarEclampsia
                    'anemia': safe_bool_none(sta(part3, 'Anemia')) or Undefined,
                    'infections_during_delivery': sta(part3, 'InfectionDuringBirth') or Undefined,
                    'infections_after_delivery': sta(part3, 'InfectionAfterBirth') or Undefined,
                    # 'funiculus': sta(part3, 'CordPatology', 'Term') or Undefined,  # rbRisarFuniculus
                    # 'afterbirth': sta(part3, 'PlacentaPatology', 'Term') or Undefined,  # rbRisarAfterbirth
                },
                'manipulations': {
                    'caul': safe_bool_none(sta(part4, 'Amniotomy')) or Undefined,
                    'calfbed': safe_bool_none(sta(part4, 'ManualWombSurvey')) or Undefined,
                    'perineotomy': sta(part4, 'Perineotomy') or Undefined,
                    'secundines': safe_bool_none(sta(part4, 'ManualRemovalAfterBirth')) or Undefined,
                    'other_manipulations': sta(part4, 'AnotherManipulations') or Undefined,
                },
                'operations': {
                    # 'caesarean_section': part5['CesarianDelivery'] or Undefined,  #rbRisarCaesarean_Section
                    # 'obstetrical_forceps': part5['Forceps'] or Undefined,  # rbRisarObstetrical_Forceps
                    # 'vacuum_extraction': safe_bool_none(part5['Vacuum']),  # boolean
                    # 'indication': part5['Indicator'] or Undefined,  # rbRisarIndication
                    # 'specialities': part5['Speciality'] or Undefined,  # rbRisarSpecialities
                    # 'anesthetization': part5['Anestesia'] or Undefined,  # rbRisarAnesthetization
                    # 'hysterectomy': part5['Hysterectomy'] or Undefined,  # rbRisarHysterectomy
                    # 'complications': part5['Complication'] or Undefined,  # MKB
                    'embryotomy': safe_bool_none(sta(part5, 'Embryotomy')) or Undefined,
                },
                'kids': []
            }

            mother_death_required = [
                "reason_of_death",
                "death_date",
                "death_time"
            ]
            mother_death = {
                'death_date': encode(sta(part2, 'MotherDeathData', 'DeathDate')),
                'death_time': (encode(sta(part2, 'MotherDeathData', 'DeathTime')) or '')[:5],
                'reason_of_death': sta(part2, 'MotherDeathData', 'MotherDeathReason'),
                # --
                # 'pat_diagnosis_osn': sta(part2, 'MotherDeathData', 'PatologicalDiagnos'),
                # 'pat_diagnosis_sop': sta(part2, 'MotherDeathData', 'AcompanyDiagnos'),
                # 'pat_diagnosis_osl': sta(part2, 'MotherDeathData', 'ComplicationDiagnos'),
                'control_expert_conclusion': sta(part2, 'LkkResult') or Undefined,
            }
            if all(mother_death[x] for x in mother_death_required):
                main_item['body']['mother_death'] = mother_death

            kids = []
            childs = part6['Child']
            for child in childs:
                # "required": ["alive", "sex", "weight", "length", "date"]
                kids.append({
                    'alive': safe_bool(sta(child, 'Alive')),
                    'sex': safe_int(sta(child, 'Gender')) - 1,
                    'weight': safe_double(sta(child, 'Weight')),
                    'length': safe_double(sta(child, 'Height')),
                    'date': encode(sta(child, 'BirthDate')),
                    # --
                    # 'time': ???,
                    # 'maturity_rate': sta(child, 'FullTerm') or Undefined,  # rbRisarMaturity_Rate
                    'apgar_score_1': safe_int(sta(child, 'Apgar_1min')) or Undefined,
                    'apgar_score_5': safe_int(sta(child, 'Apgar_5min')) or Undefined,
                    'apgar_score_10': safe_int(sta(child, 'Apgar_10min')) or Undefined,
                    'death_date': encode(sta(child, 'DeathDate')) or Undefined,
                    'death_time': (encode(sta(child, 'DeathTime')) or '')[:5] or Undefined,
                    'death_reason': sta(child, 'DeathReason') or Undefined,
                    # 'diseases': child['NewbornSeakness'] or Undefined,
                })
            main_item['body']['kids'] = kids

        return entities
