#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.lib.message import Message


class OperationResult(object):
    def check(self, method, url):
        msg = None
        op_res = self.get_operation_result()
        if op_res is not None:
            data = {'result': op_res}
            msg = Message(data)
            msg.to_local_service()
            msg.set_result_type()
            msg.set_method('put', url + 'result/')
        return msg

    def get_operation_result(self):
        # todo:
        return False
