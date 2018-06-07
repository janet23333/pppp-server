import requests

from conf import settings

url = settings['cmdb_server']['url']
token = settings['cmdb_server']['token']
api = '{}/host/?application_name='.format(url)
token = {'token': token}


def host_category(application_name, args):
    result = dict()
    key = args
    status = key['status']
    version = [_key['version'] for _key in key['application_list'] if _key['application']['name'] == application_name][0]
    application_type = [_key['application']['application_type_id'] for _key in key['application_list'] if _key['application']['name'] == application_name][0]
    hostname = key['hostname']
    ip = [ip['ip_addr'] for ip in key['network_interface'][0]['ip'] if ip['ip_type'] == 1][0]
    if application_type == 0:
        result['msg'] = '{} application_type is null'.format(application_name)
    app_type = 'mod' if application_type == 2 else 'app'
    flag_type = int(hostname.split('-')[-1]) % 2
    info = str(hostname + ' ' + str(application_type) + ' ' + application_name + ' ' + version)
    content = ip + ' #' + info
    flag = key['flag']
    if flag == 0 or flag == 3:
        result['msg'] = '{} # {} flag = 1 or 2 ,please set flag value'.format(ip, hostname)
        return result
    if status == 3:
        result['all'] = content
    if status == 5:
        result['offline'] = content
        return result
    elif status == 4:
        result['error'] = content
        return result
    elif key['flag'] == 2 and status == 3:
        result['gray'] = content
        if 'mod' in app_type:
            result['master_gray_mod'] = content
            result['gray_mod'] = content
        else:
            result['master_gray_app'] = content
            result['gray_app'] = content
        return result
    elif flag_type == 1 and status == 3 and 'mod' in app_type and flag == 1:
        result['master_mod'] = content
        result['master_gray_mod'] = content
        result['master'] = content
    elif flag_type == 1 and status == 3 and 'mod' not in app_type and flag == 1:
        result['master_app'] = content
        result['master_gray_app'] = content
        result['master'] = content
    elif flag_type == 0 and status == 3 and 'mod' in app_type and flag == 1:
        result['slave_mod'] = content
        result['slave'] = content
    elif flag_type == 0 and status == 3 and 'mod' not in app_type and flag == 1:
        result['slave_app'] = content
        result['slave'] = content
    elif status == 2:
        result['msg'] = '{} status != 3 please set status values '.format(ip, hostname)
    else:
        result['msg'] = '{} status exception  please set status values '.format(ip, hostname)
    return result


def deploy_host(application_list):
    headers = token
    result = {'result': {}, 'msg': {}}
    for application_name in application_list:
        _url = '{}{}'.format(api, application_name)
        res = requests.get(url=_url, headers=headers)
        if res.status_code == 200:
            res = res.json()['res']
            if res:
                for key in res:
                    _result = host_category(application_name, key)
                    for _key, _value in _result.items():
                        if _key == 'msg':
                            if result['msg']:
                                result['msg'].append(_value)
                            else:
                                result['msg'] = [_value]
                            break
                        if _key in result['result']:
                            result['result'][_key].append(_value)
                        else:
                            result['result'][_key] = [_value]
            else:
                    if result['msg']:
                        result['msg'].append('application name {} not bind host'.format(application_name))
                    else:
                        result['msg'] = ['application name {} not bind host'.format(application_name)]
        else:
            if result['msg']:
                result['msg'].append('application name {}: {}'.format(application_name, res.text))
            else:
                result['msg'] = ['application name {}: {}'.format(application_name, res.text)]
    return result


def set_master_slave_host(res):
    grey_host = list(filter(lambda x: x['flag'] == 2, res))
    not_grey_host = list(filter(lambda x: x['flag'] != 2, res))

    for i, item in enumerate(not_grey_host):
        if i % 2 == 0:
            item['host_deploy_type'] = 'master'
        else:
            item['host_deploy_type'] = 'slave'

    def assign_grey(x):
        x['host_deploy_type'] = "grey"
        return x

    grey_host = list(map(assign_grey, grey_host))
    not_grey_host.extend(grey_host)
    return not_grey_host
