#! coding:utf-8
"""


@author: BARS Group
@date: 21.10.2016

"""

# -*- coding: utf-8 -*-
import logging

import flask

__author__ = 'viruzzz-kun'


logger = logging.getLogger('simple')


format_exception = u'''Request:
%(method)s %(url)s
%(request_headers)s%(request_json)s

Response: %(code)i
Exception: %(exception)r
Body: %(body)s
'''

format_ok = u'''Request:
%(method)s %(url)s
%(request_headers)s%(request_json)s

Response: %(code)i
Body: %(body)s
'''


def format_logger_message(code, j, exception=None):
    data = flask.request.get_data(as_text=True, parse_form_data=True)
    d = {
        'method': flask.request.method,
        'url': flask.request.url,
        'request_headers': u'\n'.join('%s: %s' % i for i in flask.request.headers.iteritems()),
        'request_json': '\n\n%s' % data if data else '',
        'code': code,
        'exception': exception,
        'body': j,
    }
    if exception:
        return format_exception % d
    else:
        return format_ok % d


def hook(code, j, e=None, stream_id=None):
    stream_id_txt = ''
    if stream_id:
        stream_id_txt = 'stream_id: %s ' % stream_id
    if e:
        logger.error('%s' % stream_id_txt + format_logger_message(code, j))
    else:
        logger.debug('%s' % stream_id_txt + format_logger_message(code, j))
