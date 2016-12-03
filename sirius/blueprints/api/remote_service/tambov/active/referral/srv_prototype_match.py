#! coding:utf-8
"""


@author: BARS Group
@date: 01.12.2016

"""
import csv
import os


class SrvPrototypeMatch(object):
    inited = False
    srv_prototype__measure__map = {}
    srv_prototype__measure_code__map = {}
    measure__srv_prototype__map = {}
    prototype_code__srv_prototype__map = {}

    @classmethod
    def init(cls):
        if not cls.inited:
            fname = 'measure_prototype_01.csv'
            this_path = os.path.realpath(__file__)
            with open(os.path.join(os.path.dirname(this_path), fname)) as f:
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
                    measure_code = '%04d' % int(row[4])
                    if prototype_id:
                        cls.srv_prototype__measure__map[prototype_id] = (
                            measure_id, measure_type
                        )
                        cls.srv_prototype__measure_code__map[prototype_id] = (
                            measure_code, measure_type
                        )
                        if prototype_code:
                            cls.prototype_code__srv_prototype__map[prototype_code] = prototype_id
                    if measure_id:
                        cls.measure__srv_prototype__map[measure_id] = prototype_id
            cls.inited = True

    @classmethod
    def get_prototype_id(cls, measure_id):
        cls.init()
        return cls.measure__srv_prototype__map.get(measure_id)

    @classmethod
    def get_prototype_id_by_prototype_code(cls, prototype_code):
        cls.init()
        return cls.prototype_code__srv_prototype__map.get(prototype_code)

    @classmethod
    def get_measure_type(cls, prototype_id):
        cls.init()
        return cls.srv_prototype__measure__map.get(prototype_id, (0, None))[1]

    @classmethod
    def get_measure_id(cls, prototype_id):
        cls.init()
        return cls.srv_prototype__measure__map.get(prototype_id, (None,))[0]

    @classmethod
    def get_measure_code(cls, prototype_id):
        cls.init()
        return cls.srv_prototype__measure_code__map.get(prototype_id, (None,))[0]
