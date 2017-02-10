#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from hitsl_utils.enum import Enum
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.monitor.exception import InternalError
from sirius.blueprints.reformer.api import Builder, RequestEntities
from sirius.models.system import SystemCode
from sirius.models.operation import OperationCode


class RefbookTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA
    risar_refbooks = {
        'rbMeasureStatus',
        'rbResult',
        'rbFinance',
        'rbDiseaseCharacter',
        'rbDispanser',
        'rbTraumaType',
        'rbConditionMedHelp',
        'rbProfMedHelp',
        'rbAcheResult',
        'rbSpeciality',
        'rbPost',
    }
    vesta_refbooks = {
        'rbRisarPregnancy_Final',
        'rbRisarAbort',
        'rbRisarDelivery_Waters',
        'rbRisarWeakness',
        'rbRisarEclampsia',
        'rbRisarFuniculus',
        'rbRisarAfterbirth',
        'rbRisarCaesarean_Section',
        'rbRisarObstetrical_Forceps',
        'rbRisarIndication',
        'rbRisarSpecialities',
        'rbRisarAnesthetization',
        'rbRisarHysterectomy',
        'rbRisarMaturity_Rate',
        'rbRisarMedicalCare',
        'rbRisarFinishedTreatment',
        'rbRisarInitialTreatment',
        'rbRisarOperationAnesthetization',
        'rbRisarOperationEquipment',
        'rbRisarSickLeaveType',
        'rbRisarSickLeaveReason',
    }

    def build_local_entities(self, header_meta, data):
        src_operation_code = self.get_operation_code_by_method(header_meta['remote_method'])
        rb_code = header_meta['remote_parents_params']['rb_code']['id']
        parents_params = {
            'rb_code': {'entity': RisarEntityCode.RISAR_REFBOOK_NAME, 'id': rb_code}
        }
        entities = RequestEntities(self.reformer.stream_id)
        if rb_code in self.risar_refbooks:
            main_item = entities.set_main_entity(
                dst_entity_code=RisarEntityCode.RISAR_REFBOOK,
                dst_parents_params=parents_params,
                dst_main_id_name='code',
                dst_id_prefix=rb_code,
                src_operation_code=src_operation_code,
                src_entity_code=header_meta['remote_entity_code'],
                src_main_id_name=header_meta['remote_main_param_name'],
                src_id_prefix=rb_code,
                src_id=header_meta['remote_main_id'],
                level_count=1,
            )
            if src_operation_code != OperationCode.DELETE:
                main_item['body'] = data
        elif rb_code in self.vesta_refbooks:
            # заглушка для справочников весты
            pass
        else:
            raise InternalError(
                'Unknown reference_book_code (%s)' % rb_code)

        return entities
