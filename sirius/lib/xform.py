# -*- coding: utf-8 -*-
import functools
import logging
import jsonschema
from abc import ABCMeta
from sirius.blueprints.api.remote_service.producer import RemoteProducer

from sirius.lib.apiutils import ApiException
from sirius.lib.message import Message

logger = logging.getLogger('simple')


INTERNAL_ERROR = 500
VALIDATION_ERROR = 400
NOT_FOUND_ERROR = 404
ALREADY_PRESENT_ERROR = 409
MIS_BARS_CODE = 'Mis-Bars'


def none_default(function=None, default=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 0 and args[-1] is None:
                if callable(default):
                    return default()
            else:
                return func(*args, **kwargs)
        return wrapper
    if callable(function):
        return decorator(function)
    return decorator


class Undefined(object):
    pass


def wrap_simplify(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return simplify(func(*args, **kwargs))
    return wrapper


def simplify(o):
    if isinstance(o, dict):
        return simplify_dict(o)
    elif isinstance(o, list):
        return simplify_list(o)
    return o


def simplify_dict(d):
    return {
        key: simplify(value)
        for key, value in d.iteritems()
        if value is not Undefined
    }


def simplify_list(l):
    return [
        simplify(item)
        for item in l
        if item is not Undefined
    ]


class XForm(object):
    __metaclass__ = ABCMeta
    schema = None
    parent_obj_class = None
    target_obj_class = None
    parent_id_required = True
    target_id_required = True
    remote_system_code = None
    entity_code = None

    def __init__(self, api_version, is_create=False):
        self.version = 0
        self.new = is_create
        self.parent_obj_id = None
        self.target_obj_id = None
        self.parent_obj = None
        self.target_obj = None
        self.pcard = None
        self._changed = []
        self._deleted = []

        self.set_version(api_version)

    def set_version(self, version):
        for v in xrange(self.version + 1, version + 1):
            method = getattr(self, 'set_version_%i' % v, None)
            if method is None:
                raise ApiException(VALIDATION_ERROR, 'Version %i of API is unsupported' % (version, ))
            else:
                method()
        self.version = version

    def validate(self, data):
        if data is None:
            raise ApiException(VALIDATION_ERROR, 'No JSON body')
        schema = self.schema[self.version]
        cls = jsonschema.validators.validator_for(schema)
        val = cls(schema)
        errors = [{
            'error': error.message,
            'instance': error.instance,
            'path': '/' + '/'.join(map(unicode, error.absolute_path)),
        } for error in val.iter_errors(data)]
        if errors:
            raise ApiException(
                VALIDATION_ERROR,
                'Validation error',
                errors=errors,
            )

    def send_messages(self, entity_id, param_name, data, service_name, method_code):
        msg = Message(data)
        msg.to_local_service()
        msg.set_send_data_type()
        msg.get_header().meta.update({
            'remote_system_code': self.remote_system_code,
            'remote_entity_code': self.entity_code,
            'remote_service_code': service_name,
            'remote_main_id': entity_id,
            'remote_main_param_name': param_name,
            'remote_method': method_code,
        })

        # todo: цикл вложенных дозапросов и связывание ответов
        # from sirius.lib.implement import Implementation
        # implement = Implementation()
        # reformer = implement.get_reformer(remote_system_code)
        # miss_reqs = reformer.get_missing_requests(msg)
        # miss_data = reformer.transfer_give_data(miss_reqs)
        # msg.add_missing_data(miss_data)

        # data_store = Difference()

        producer = RemoteProducer()
        producer.send(msg)
