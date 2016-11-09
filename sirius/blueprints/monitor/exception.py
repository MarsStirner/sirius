#! coding:utf-8
"""


@author: BARS Group
@date: 24.10.2016

"""
import sys
import traceback
import functools
from time import time, sleep
from datetime import datetime
import logging

import flask
from requests import ConnectionError
from six import reraise

from sirius.lib.apiutils import ApiException, jsonify_api_exception, \
    jsonify_exception, RawApiResult, jsonify_ok, json_dumps
from sqlalchemy.exc import OperationalError as SAOperationalError
from zeep.exceptions import TransportError, Error as ZeepError

logger = logging.getLogger('simple')


class LoggedException(Exception):
    """Залогированное исключение"""
    pass


class InternalError(StandardError):
    pass


class ExternalError(StandardError):
    pass


class ConnectError(StandardError):
    pass


def module_entry(function=None, stream_pos=2, self_pos=1):
    """
    Ловит ошибку на входе в модуль, собирая входные данные
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = meta = module = obj = None
            enter_datetime = datetime.today()
            enter_time = time()
            try:
                module = type(args[self_pos - 1])
                obj = args[stream_pos - 1]
                meta = module.get_stream_meta(obj)
                res = func(*args, **kwargs)
                exit_time = time()
            except (StandardError, ZeepError) as exc:
                error_datetime = datetime.today()
                traceback.print_exc()
                message = traceback.format_exception_only(type(exc), exc)[-1]
                params = {
                    'stream': get_stream_data(module, func, obj, meta),
                    'message': message,
                    'enter_time': enter_datetime,
                    'error_time': error_datetime,
                    'traceback': traceback.format_exc(),
                }
                logger.error(params_to_str(params))
                # logg_to_MonitorDB(params)
                reraise(Exception, LoggedException(params), sys.exc_info()[2])
            else:
                params = {
                    'stream': get_stream_data(module, func, obj, meta),
                    'message': 'OK',
                    'enter_time': enter_datetime,
                    'work_time': exit_time - enter_time,
                }
                logger.info(unicode(params))
                # logg_to_MonitorDB(params)
            return res
        return wrapper
    if callable(function):
        return decorator(function)
    return decorator


def params_to_str(params):
    r = '\n'.join([': '.join((k.upper(), str(v))) for k, v in params.items()])
    return r.decode('utf-8')


def task_entry(function=None, stream_pos=2, self_pos=1):
    """
    Ловит ошибку на входе в таск, собирая входные данные
    """
    sleep_timeout = 6

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = meta = module = obj = None
            enter_datetime = datetime.today()
            enter_time = time()
            # task = args[self_pos - 1]
            # if task.request.called_directly:  # task.request.is_eager
            retry = True
            retry_count = 0
            max_retry = 5
            while retry:
                retry = False
                retry_count += 1
                try:
                    module = type(args[self_pos - 1])
                    if stream_pos is not None:
                        obj = args[stream_pos - 1]
                        meta = {'header': vars(obj.get_header())}
                    res = func(*args, **kwargs)
                    exit_time = time()
                except LoggedException as exc:
                    reraise(Exception, LoggedException(exc.args[0]), sys.exc_info()[2])
                except SAOperationalError as exc:
                    logger.error(unicode(exc))
                    # logg_to_MonitorDB(params)
                    if retry_count > max_retry:
                        # todo: stop celery workers (back rabbit msg)
                        pass
                    retry = True
                    sleep(sleep_timeout)
                except Exception as exc:
                    error_datetime = datetime.today()
                    traceback.print_exc()
                    message = traceback.format_exception_only(type(exc), exc)[-1]
                    params = {
                        'stream': get_stream_data(module, func, obj, meta),
                        'message': message,
                        'enter_time': enter_datetime,
                        'error_time': error_datetime,
                        'traceback': traceback.format_exc(),
                    }
                    logger.error(params_to_str(params))
                    # logg_to_MonitorDB(params)
                    reraise(Exception, LoggedException(params), sys.exc_info()[2])
                else:
                    params = {
                        'stream': get_stream_data(module, func, obj, meta),
                        'message': 'OK',
                        'enter_time': enter_datetime,
                        'work_time': exit_time - enter_time,
                    }
                    logger.info(unicode(params))
                    # logg_to_MonitorDB(params)
            return res
        return wrapper
    if callable(function):
        return decorator(function)
    return decorator


def beat_entry(function=None, self_pos=1):
    """
    Ловит ошибку на входе в планировщик задач (celery beat)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = meta = module = obj = None
            enter_datetime = datetime.today()
            enter_time = time()
            task = args[self_pos - 1]
            # if task.request.called_directly:  # task.request.is_eager
            try:
                module = type(args[self_pos - 1])
                res = func(*args, **kwargs)
                exit_time = time()
            except LoggedException as exc:
                reraise(Exception, LoggedException(exc.args[0]), sys.exc_info()[2])
            except Exception as exc:
                error_datetime = datetime.today()
                traceback.print_exc()
                message = traceback.format_exception_only(type(exc), exc)[-1]
                params = {
                    'stream': get_stream_data(module, func, obj, meta),
                    'message': message,
                    'enter_time': enter_datetime,
                    'error_time': error_datetime,
                    'traceback': traceback.format_exc(),
                }
                logger.error(params_to_str(params))
                # logg_to_MonitorDB(params)
                reraise(Exception, LoggedException(params), sys.exc_info()[2])
            else:
                params = {
                    'stream': get_stream_data(module, func, obj, meta),
                    'message': 'OK',
                    'enter_time': enter_datetime,
                    'work_time': exit_time - enter_time,
                }
                logger.info(unicode(params))
                # logg_to_MonitorDB(params)
            return res
        return wrapper
    if callable(function):
        return decorator(function)
    return decorator


def connect_entry(function=None, login=None):
    """
    Ловит ошибку на входе в модуль активных запросов
    """
    sleep_timeout = 6

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = None
            retry = True
            retry_count = 0
            max_retry = 5
            while retry:
                retry = False
                retry_count += 1
                try:
                    if callable(login):
                        session = getattr(func, '_session', None)
                        if not session:
                            session = login()
                            func._session = session
                        kwargs['session'] = session
                    res = func(*args, **kwargs)
                except (ConnectError, ConnectionError) as exc:
                    traceback.print_exc()
                    logger.error(str(exc))
                    # logg_to_MonitorDB(params)
                    if retry_count > max_retry:
                        # todo: stop celery workers (back rabbit msg)
                        pass
                    retry = True
                    sleep(sleep_timeout)
                except (TransportError,) as exc:
                    if retry_count == 1 and callable(login):  #and res.status_code == 403:
                        func._session = None
                        retry = True
            return res
        return wrapper
    if callable(function):
        return decorator(function)
    return decorator


def get_stream_data(module, func, obj, meta):
    return {
        'module': module and module.__name__,
        'method': func and func.__name__,
        'stream type': obj and type(obj),
        'meta': meta,
    }


def local_api_method(func=None, hook=None, authorization=False):
    """Декоратор API-функции. Автомагически оборачивает результат или исключение в jsonify-ответ
    :param func: декорируемая функция
    :type func: callable
    :param hook: Response hook
    :type: callable
    """
    def decorator(func):
        if authorization:
            func.is_api = True
        else:
            func.is_public_api = True

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except ApiException, e:
                traceback.print_exc()
                j, code, headers = jsonify_api_exception(e, traceback.extract_tb(sys.exc_info()[2]))
                if hook:
                    hook(code, j, e)
                # logg_to_MonitorDB(params)
            except LoggedException, e:
                j, code, headers = jsonify_exception(e, traceback.extract_tb(sys.exc_info()[2]))
            except Exception, e:
                traceback.print_exc()
                j, code, headers = jsonify_exception(e, traceback.extract_tb(sys.exc_info()[2]))
                if hook:
                    hook(code, j, e)
                # logg_to_MonitorDB(params)
            else:
                if isinstance(result, RawApiResult):
                    j, code, headers = jsonify_ok(result.obj, result.result_code, result.result_name)
                    if result.extra_headers:
                        headers.update(result.extra_headers)
                else:
                    j, code, headers = jsonify_ok(result)
                if hook:
                    hook(code, j)
                # logg_to_MonitorDB(params)
            return flask.make_response(j, code, headers)

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def remote_api_method(func=None, hook=None, authorization=False):
    """Декоратор API-функции. Автомагически оборачивает результат или исключение в jsonify-ответ
    :param func: декорируемая функция
    :type func: callable
    :param hook: Response hook
    :type: callable
    """
    def decorator(func):
        if authorization:
            func.is_api = True
        else:
            func.is_public_api = True

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except ApiException, e:
                traceback.print_exc()
                j, code, headers = jsonify_api_exception(e, traceback.extract_tb(sys.exc_info()[2]))
                if hook:
                    hook(code, j, e)
                # logg_to_MonitorDB(params)
            except LoggedException, e:
                params = e.args[0]
                exc = InternalError(params['message'])
                j, code, headers = jsonify_exception(exc, traceback.extract_tb(sys.exc_info()[2]))
            except Exception, e:
                traceback.print_exc()
                exc = InternalError(str(e))
                j, code, headers = jsonify_exception(exc, traceback.extract_tb(sys.exc_info()[2]))
                if hook:
                    hook(code, j, e)
                # logg_to_MonitorDB(params)
            else:
                if isinstance(result, RawApiResult):
                    j, code, headers = jsonify_ok(result.obj, result.result_code, result.result_name)
                    if result.extra_headers:
                        headers.update(result.extra_headers)
                else:
                    j, code, headers = jsonify_ok(result)
                if hook:
                    hook(code, j)
                # logg_to_MonitorDB(params)
            return flask.make_response(j, code, headers)

        return wrapper

    if func is None:
        return decorator
    return decorator(func)
