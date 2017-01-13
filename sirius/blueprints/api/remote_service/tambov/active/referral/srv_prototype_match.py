#! coding:utf-8
"""


@author: BARS Group
@date: 01.12.2016

"""
import csv
import os
from sirius.blueprints.monitor.exception import InternalError


class SrvPrototypeMatch(object):
    inited = False
    # fname = 'measure_prototype_01.csv'
    fname = 'measure_prototype_01_skiped_fake.csv'
    srv_prototype__measure__map = {}
    srv_prototype__measure_code__map = {}
    measure__srv_prototype__map = {}
    prototype_code__srv_prototype__map = {}
    measure_code__srv_prototype__map = {}

    @classmethod
    def init(cls):
        if not cls.inited:
            this_path = os.path.realpath(__file__)
            with open(os.path.join(os.path.dirname(this_path), cls.fname)) as f:
                rows = csv.reader(f, delimiter='#')
                header = False
                for row in rows:
                    if not header:
                        header = True
                        continue
                    measure_id = row[0]
                    measure_type = row[1]
                    prototype_id = row[2]
                    prototype_code = row[3]
                    measure_code = row[4] and '%04d' % int(row[4])
                    if prototype_id:
                        cls.srv_prototype__measure__map[prototype_id] = (
                            measure_id, measure_type
                        )
                        cls.srv_prototype__measure_code__map[prototype_id] = (
                            measure_code, measure_type
                        )
                        if prototype_code:
                            cls.prototype_code__srv_prototype__map[prototype_code] = prototype_id
                    # if measure_id:
                    #     cls.measure__srv_prototype__map[measure_id] = prototype_id
                    if measure_code:
                        cls.measure_code__srv_prototype__map[measure_code] = prototype_id
            cls.inited = True

    # @classmethod
    # def get_prototype_id(cls, measure_id):
    #     cls.init()
    #     res = cls.measure__srv_prototype__map.get(measure_id)
    #     if not res:
    #         raise InternalError(
    #             'For measure_id (%s) not found match prototype_id in "%s" file' %
    #             (measure_id, cls.fname)
    #         )
    #     return res

    @classmethod
    def get_prototype_id_by_mes_code(cls, measure_code, error_ignore=False):
        cls.init()
        res = cls.measure_code__srv_prototype__map.get(measure_code)
        if not res and not error_ignore:
            raise InternalError(
                'For measure_code (%s) not found match prototype_id in "%s" file' %
                (measure_code, cls.fname)
            )
        return res

    @classmethod
    def get_prototype_id_by_prototype_code(cls, prototype_code):
        cls.init()
        res = cls.prototype_code__srv_prototype__map.get(prototype_code)
        if not res:
            raise InternalError(
                'For prototype_code (%s) not found match prototype_id in "%s" file' %
                (prototype_code, cls.fname)
            )
        return res

    @classmethod
    def get_measure_type(cls, prototype_id):
        cls.init()
        res = cls.srv_prototype__measure__map.get(prototype_id, (0, None))[1]
        if not res:
            raise InternalError(
                'For prototype_id (%s) not found match measure_type in "%s" file' %
                (prototype_id, cls.fname)
            )
        return res

    # @classmethod
    # def get_measure_id(cls, prototype_id):
    #     cls.init()
    #     res = cls.srv_prototype__measure__map.get(prototype_id, (None,))[0]
    #     if not res:
    #         raise InternalError(
    #             'For prototype_id (%s) not found match measure_id in "%s" file' %
    #             (prototype_id, cls.fname)
    #         )
    #     return res

    @classmethod
    def get_measure_code(cls, prototype_id, error_ignore=False):
        cls.init()
        res = cls.srv_prototype__measure_code__map.get(prototype_id, (None,))[0]
        if not res and not error_ignore:
            raise InternalError(
                'For prototype_id (%s) not found match measure_code in "%s" file' %
                (prototype_id, cls.fname)
            )
        return res
