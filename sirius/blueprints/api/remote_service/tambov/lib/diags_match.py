#! coding:utf-8
"""


@author: BARS Group
@date: 01.12.2016

"""
import csv
import os
from sirius.blueprints.monitor.exception import InternalError


class DiagsMatch(object):
    inited = False
    fname = 'diags_ids.csv'
    code__id__map = {}
    id__code__map = {}

    @classmethod
    def init(cls):
        if not cls.inited:
            this_path = os.path.realpath(__file__)
            with open(os.path.join(os.path.dirname(this_path), cls.fname)) as f:
                rows = csv.reader(f, delimiter='#')
                header = False
                for row in rows:
                    # if not header:
                    #     header = True
                    #     continue
                    diag_id = row[0]
                    diag_code = row[1]
                    cls.id__code__map[diag_id] = diag_code
                    cls.code__id__map[diag_code] = diag_id
            cls.inited = True

    @classmethod
    def diag_id(cls, diag_code):
        cls.init()
        res = cls.code__id__map.get(diag_code)
        if not res:
            raise InternalError(
                'For diag_code (%s) not found match diag_id in "%s" file' %
                (diag_code, cls.fname)
            )
        return res

    @classmethod
    def diag_code(cls, diag_id):
        cls.init()
        res = cls.id__code__map.get(diag_id)
        if not res:
            raise InternalError(
                'For diag_id (%s) not found match diag_code in "%s" file' %
                (diag_id, cls.fname)
            )
        return res

    @classmethod
    def safe_diag_id(cls, diag_code):
        if not diag_code:
            return
        return cls.diag_id(diag_code)

    @classmethod
    def safe_diag_code(cls, diag_id):
        if not diag_id:
            return
        return cls.diag_code(diag_id)
