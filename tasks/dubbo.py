import requests
from celery.utils.log import get_task_logger
from celery_worker import app
from conf import settings
from tasks.base import DubboTask
import time
from json.decoder import JSONDecodeError

logger = get_task_logger(__name__)

dubbo_admin_settings = settings['dubbo_admin']

AUTH_KEY = dubbo_admin_settings['authkey']
YUNNEX_ADMIN_URL = dubbo_admin_settings['yunnex_admin_url']


class DubboError(Exception):
    pass


def error_correct_service_name(app_name, check_origin_name=True):
    # 修复错误的名字
    error_name = dubbo_admin_settings['error_name'].get('app_name')
    if error_name:
        return error_name
    # 部分应用，只能按照ip
    if check_origin_name and app_name in dubbo_admin_settings['origin_name']:
        return None
    return app_name


def _status(host, project_name, **kwargs):
    logger.info(kwargs)
    app_name = error_correct_service_name(project_name, check_origin_name=False)
    params = {
        'authkey': AUTH_KEY,
        'ip': host
    }
    if app_name is not None and app_name not in dubbo_admin_settings['origin_name']:
        params['app'] = app_name
    logger.info(params)

    request_url = '{admin_host}/dubbo/app/list'.format(admin_host=YUNNEX_ADMIN_URL)
    try:
        res = requests.get(request_url, params=params).json()
    except JSONDecodeError:
        raise DubboError('dubbo接口返回格式错误: %s' % res.text)

    logger.info(res)
    if res['success']:
        attach = res['attach']
        for provider in attach:
            if provider['name'] == app_name:
                return provider
        raise DubboError('没有匹配的应用: %s\nResponse: %s' % (app_name, res))
    else:
        if '没有找到匹配的应用' in res['reason']:
            return res['reason']
        raise DubboError(res)


@app.task(base=DubboTask)
def status(host, project_name, **kwargs):
    return _status(host, project_name, **kwargs)


@app.task(base=DubboTask)
def enable(host, project_name, **kwargs):
    logger.info(kwargs)
    app_name = error_correct_service_name(project_name)

    params = {
        'authkey': AUTH_KEY,
        'ip': host,
        'action': 'enable'
    }
    if app_name is not None:
        params['app'] = app_name
    logger.info(params)

    request_url = '{admin_host}/dubbo/app/switch2'.format(admin_host=YUNNEX_ADMIN_URL)
    try:
        res = requests.get(request_url, params=params).json()
    except JSONDecodeError:
        raise DubboError('dubbo接口返回格式错误: %s' % res.text)
    logger.info(res)
    if not res['success']:
        if '没有找到匹配的应用' in res['reason']:
            return res['reason']
        raise DubboError(res)

    return _check_dubbo_status(host, project_name, True)


@app.task(base=DubboTask)
def disable(host, project_name, **kwargs):
    logger.info(kwargs)
    app_name = error_correct_service_name(project_name)
    params = {
        'authkey': AUTH_KEY,
        'ip': host,
        'action': 'disable'
    }
    if app_name is not None:
        params['app'] = app_name
    logger.info(params)

    request_url = '{admin_host}/dubbo/app/switch2'.format(admin_host=YUNNEX_ADMIN_URL)
    try:
        res = requests.get(request_url, params=params).json()
    except JSONDecodeError:
        raise DubboError('dubbo接口返回格式错误: %s' % res.text)
    logger.info(res)
    if not res['success']:
        if '没有找到匹配的应用' in res['reason']:
            return res['reason']
        raise DubboError(res)

    return _check_dubbo_status(host, project_name, False)


def _check_dubbo_status(host, project_name, is_enable, retry_num=3):
    sleep_time = 1
    for i in range(retry_num):
        try:
            status_res = _status(host, project_name)
            if status_res and status_res.get('enable') is is_enable:
                return status_res
        except DubboError as e:
            logger.error(str(e))
            if i == retry_num - 1:
                raise e

        time.sleep(sleep_time)
        sleep_time += 1
