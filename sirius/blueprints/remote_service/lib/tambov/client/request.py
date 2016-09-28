#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""


def create(session, method, url, data):
    url = u'/risar/api/integration/0/card/%s/checkup/obs/first/' % card_id
    result = make_api_request('post', url, session, data)
    return result
