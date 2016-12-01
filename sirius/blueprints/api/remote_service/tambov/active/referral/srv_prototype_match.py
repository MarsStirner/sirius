#! coding:utf-8
"""


@author: BARS Group
@date: 01.12.2016

"""
srv_prototype__measure__map = {
    '5338': ('1', 'checkup'),
    '788': ('2', 'lab_test'),
}
measure__srv_prototype__map = dict((v[0], k) for k, v in srv_prototype__measure__map.iteritems())


class SrvPrototypeMatch(object):

    @classmethod
    def get_prototype_id(cls, measure_id):
        return measure__srv_prototype__map[measure_id]

    @classmethod
    def get_measure_type(cls, prototype_id):
        return srv_prototype__measure__map[prototype_id][1]

    @classmethod
    def get_measure_id(cls, prototype_id):
        return srv_prototype__measure__map[prototype_id][0]
