#! coding:utf-8
"""


@author: BARS Group
@date: 09.02.2017

"""
from uuid import uuid1
from hashlib import md5


def get_stream_id():
    return 'stream_' + md5(uuid1().get_hex()).hexdigest()[:10]
