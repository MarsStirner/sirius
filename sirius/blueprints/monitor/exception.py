#! coding:utf-8
"""


@author: BARS Group
@date: 24.10.2016

"""
import sys
import traceback
import functools
from time import time, sleep
from datetime import datetime, timedelta
import logging

import flask
from copy import deepcopy
from requests import ConnectionError
from sirius.app import app
from sirius.extensions import db
from six import reraise

from sirius.lib.apiutils import ApiException, jsonify_api_exception, \
    jsonify_exception, RawApiResult, jsonify_ok, json_dumps
from sqlalchemy.exc import OperationalError as SAOperationalError
from zeep.exceptions import TransportError as ZeepTransportError, Error as ZeepError, Fault as ZeepFault
# from suds import WebFault as SudsError
# from suds.transport import TransportError as SudsTransportError
from zeep.exceptions import TransportError as SudsTransportError, Error as SudsError  # заглушка (вдруг понадобится suds)

logger = logging.getLogger('simple')


class EncodeArgError(object):
    def __init__(self, *args, **kwargs):
        args_m = list(args)
        try:
            args_m[0] = args[0].encode('utf-8')
        except IndexError:
            self.message = self.__class__.__name__
        except UnicodeError:
            self.message = args_m[0]
        else:
            self.message = args_m[0]
        super(EncodeArgError, self).__init__(*tuple(args_m), **kwargs)


class LoggedException(EncodeArgError, Exception):
    """Залогированное исключение"""
    def __repr__(self):
        return self.message


class InternalError(EncodeArgError, StandardError):
    pass


class ExternalError(EncodeArgError, StandardError):
    pass


class ConnectError(EncodeArgError, StandardError):
    pass


def module_entry(function=None, stream_pos=2, self_pos=1):
    """
    Ловит ошибку на входе в модуль, собирая входные данные
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = meta = body = module = obj = None
            enter_datetime = datetime.today()
            enter_time = time()
            try:
                module = type(args[self_pos - 1])
                obj = args[stream_pos - 1]
                meta = obj.get_stream_meta()
                body = obj.get_stream_body()
                res = func(*args, **kwargs)
                exit_time = time()
            except (StandardError, ZeepError, SudsError) as exc:
                error_datetime = datetime.today()
                # traceback.print_exc()
                if isinstance(exc, ZeepFault):
                    message = ': '.join((exc.code, exc.message))
                elif isinstance(exc, ZeepError):
                    message = ': '.join((type(exc).__name__, exc.message))
                else:
                    message = traceback.format_exception_only(type(exc), exc)[-1].decode('utf-8')
                params = {
                    'stream': get_stream_data(module, func, obj, meta, body),
                    'message': message,
                    'enter_time': enter_datetime,
                    'error_time': error_datetime,
                    'traceback': traceback.format_exc().decode('utf-8'),
                }
                logger.error(params_to_str(params))
                # logg_to_MonitorDB(params)
                reraise(Exception, LoggedException(message), sys.exc_info()[2])
            else:
                params = {
                    'stream': get_stream_data(module, func, obj, meta),
                    'message': 'OK',
                    'enter_time': enter_datetime,
                    'work_time': exit_time - enter_time,
                }
                logger.info(params_to_str(params))
                # logg_to_MonitorDB(params)
            return res
        return wrapper
    if callable(function):
        return decorator(function)
    return decorator


def check_point(function=None, stream_pos=2, self_pos=1):
    """
    Ловит ошибку в ходе итерации, собирая данные по элементу
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = meta = body = module = obj = None
            enter_datetime = datetime.today()
            enter_time = time()
            try:
                module = type(args[self_pos - 1])
                obj = args[stream_pos - 1]
                meta = obj.get_stream_meta()
                body = obj.get_stream_body()
                res = func(*args, **kwargs)
                exit_time = time()
            except (StandardError, ZeepError, SudsError) as exc:
                error_datetime = datetime.today()
                # traceback.print_exc()
                if isinstance(exc, ZeepFault):
                    message = ': '.join((exc.code, exc.message))
                elif isinstance(exc, ZeepError):
                    message = ': '.join((type(exc).__name__, exc.message))
                else:
                    message = traceback.format_exception_only(type(exc), exc)[-1].decode('utf-8')
                params = {
                    'stream': get_stream_data(module, func, obj, meta, body),
                    'message': message,
                    'enter_time': enter_datetime,
                    'error_time': error_datetime,
                    'traceback': traceback.format_exc().decode('utf-8'),
                }
                logger.error(params_to_str(params))
                # logg_to_MonitorDB(params)
                reraise(Exception, LoggedException(message), sys.exc_info()[2])
            return res
        return wrapper
    if callable(function):
        return decorator(function)
    return decorator


def params_to_str(params):
    r = '\n'.join([': '.join(
        (k.upper(), prepare_objects(v))
    ) for k, v in params.items()])
    return r


def prepare_objects(d):
    pr_objs = set()

    def deep_cleaner(o, pre_o=None, pre_k=None):
        if isinstance(o, dict):
            if id(o) in pr_objs:
                if pre_o:
                    # str_o = unicode(o)
                    pre_o[pre_k] = u'...'
                return
            pr_objs.add(id(o))
            for k, v in o.iteritems():
                if callable(v):
                    o[k] = unicode(v)
                deep_cleaner(v, o, k)
            pr_objs.remove(id(o))
        if isinstance(o, (list, tuple)):
            map(deep_cleaner, o)
    if isinstance(d, dict):
        dc = deepcopy(d)
        deep_cleaner(dc)
        dc = json_dumps(dc)
    else:
        dc = unicode(d)
    return dc


def task_entry(function=None, stream_pos=1, self_pos=2):
    """
    Ловит ошибку на входе в таск, собирая входные данные
    """
    sleep_timeout = 6

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = meta = body = module = obj = None
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
                    if len(args) >= self_pos:
                        module = type(args[self_pos - 1])
                    if stream_pos is not None:
                        obj = args[stream_pos - 1]
                        meta = obj.get_stream_meta()
                        body = obj.get_stream_body()
                    res = func(*args, **kwargs)
                    exit_time = time()
                except LoggedException as exc:
                    db.session.rollback()
                    raise
                except SAOperationalError as exc:
                    logger.error(unicode(exc))
                    # logg_to_MonitorDB(params)
                    if retry_count > max_retry:
                        # todo: stop celery workers (back rabbit msg)
                        db.session.rollback()
                    retry = True
                    sleep(sleep_timeout)
                except Exception as exc:
                    if isinstance(exc, ApiException):
                        if exc.code == 200:
                            raise
                    db.session.rollback()
                    error_datetime = datetime.today()
                    # traceback.print_exc()
                    message = traceback.format_exception_only(type(exc), exc)[-1].decode('utf-8')
                    params = {
                        'stream': get_stream_data(module, func, obj, meta, body),
                        'message': message,
                        'enter_time': enter_datetime,
                        'error_time': error_datetime,
                        'traceback': traceback.format_exc().decode('utf-8'),
                    }
                    logger.error(params_to_str(params))
                    # logg_to_MonitorDB(params)
                    reraise(Exception, LoggedException(message), sys.exc_info()[2])
                else:
                    params = {
                        'stream': get_stream_data(module, func, obj, meta),
                        'message': 'OK',
                        'enter_time': enter_datetime,
                        'work_time': exit_time - enter_time,
                    }
                    logger.info(params_to_str(params))
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
                db.session.rollback()
                raise
            except Exception as exc:
                db.session.rollback()
                error_datetime = datetime.today()
                # traceback.print_exc()
                message = traceback.format_exception_only(type(exc), exc)[-1].decode('utf-8')
                params = {
                    'stream': get_stream_data(module, func, obj, meta),
                    'message': message,
                    'enter_time': enter_datetime,
                    'error_time': error_datetime,
                    'traceback': traceback.format_exc().decode('utf-8'),
                }
                logger.error(params_to_str(params))
                # logg_to_MonitorDB(params)
                reraise(Exception, LoggedException(message), sys.exc_info()[2])
            else:
                # params = {
                #     'stream': get_stream_data(module, func, obj, meta),
                #     'message': 'OK',
                #     'enter_time': enter_datetime,
                #     'work_time': exit_time - enter_time,
                # }
                # logger.info(unicode(params))
                # logg_to_MonitorDB(params)
                pass
            return res
        return wrapper
    if callable(function):
        return decorator(function)
    return decorator


def connect_entry(function=None, login=None, nowait=False):
    """
    Ловит ошибку на входе в модуль активных запросов
    """
    begin_sleep_timeout = app.config['CONNECT_SLEEP_TIMEOUT']  # sec
    max_retry = app.config['CONNECT_MAX_RETRY']
    session_timeout = app.config['CONNECT_SESSION_TIMEOUT']  # min

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = None
            retry = True
            retry_count = 0
            sleep_timeout = begin_sleep_timeout
            while retry:
                retry = False
                retry_count += 1
                try:
                    if callable(login):
                        # todo: переделать на явное хранение и передачу session
                        im_func = getattr(func, 'im_func', func)
                        session, dtime = getattr(im_func, '_session', (None, None))
                        if not session or (
                            (datetime.today() - dtime) > timedelta(minutes=session_timeout)
                        ):
                            session = login()
                        dtime = datetime.today()
                        # считаем, что сессия стареет с последнего доступа
                        im_func._session = session, dtime
                        kwargs['session'] = session
                    res = func(*args, **kwargs)
                except (ConnectError, ConnectionError) as exc:
                    # traceback.print_exc()
                    try:
                        exc_txt = str(exc)
                    except (IndexError, UnicodeError):
                        exc_txt = exc.__name__
                    logger.error(exc_txt)
                    # logg_to_MonitorDB(params)
                    if retry_count > max_retry:
                        # todo: stop celery workers (back rabbit msg)
                        pass
                    if nowait:
                        reraise(Exception, exc, sys.exc_info()[2])
                    else:
                        retry = True
                        logger.info('Retry count = %s. Wait for %s seconds and then try again' % (retry_count, sleep_timeout))
                        sleep(sleep_timeout)
                        if sleep_timeout < 10 * 60:  # min
                            sleep_timeout *= 2
                except (ZeepTransportError, SudsTransportError) as exc:
                    if retry_count == 1 and callable(login):  #and res.status_code == 403:
                        im_func._session = None
                        retry = True
            return res
        return wrapper
    if callable(function):
        return decorator(function)
    return decorator


def get_stream_data(module, func, obj, meta, body=None):
    return {
        'module': module and module.__name__,
        'method': func and func.__name__,
        'stream type': obj and type(obj).__name__,
        'meta': meta,
        'body': body,
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
                j, code, headers = jsonify_exception(e, traceback.extract_tb(sys.exc_info()[2]))
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
