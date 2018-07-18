from common.sdk.ansible import exec_ansible
from common.sdk.cmdb_sdk import CmdbSdk
from conf import settings

url = settings['cmdb_server']['url']
token = settings['cmdb_server']['token']
CMDB = CmdbSdk(host=url, token=token)


def run_ansible(cmdstr, host, become=False, become_user=None, module='script'):
    tasks = [
        dict(action=dict(module=module, args=cmdstr), register='shell_out'),
        # dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
    ]
    result = exec_ansible(
        host=host,
        tasks=tasks,
        remote_user='product',
        become=become,
        become_user=become_user
    )

    return result


def get_cmdb_application_type():
    cmdb_application_type_dict = dict()
    res = CMDB.get('application_type')
    for ii in res:
        cmdb_application_type_dict.update({ii['id']: ii['name']})
    return cmdb_application_type_dict


def get_cmdb_host(kwargus):
    res = CMDB.get('host?page=1&page_size=100000', **kwargus)
    return res


def get_cmdb_host_application(kwargus):
    res = CMDB.get('host_application_multiple?page=1&page_size=100000', **kwargus)
    return res


def get_pkg_type(application_name, cmdb_application_type_dict=None):
    # 判断部署类型mod|app
    if not cmdb_application_type_dict:
        cmdb_application_type_dict = get_cmdb_application_type()
    res = CMDB.get('application', name=application_name)
    res_list = []
    for jj in res:
        application_type_id = jj['application_type_id']
        application_type_name = cmdb_application_type_dict[application_type_id]
        res_list.append({
            'type': application_type_name,
            'name': jj['name']
        })
    return res_list


def check_status(status_list):
    """用于检查pattern_host/pattern状态"""

    # 执行中
    if 1 in status_list:
        status = 1
    # 失败
    elif 3 in status_list:
        status = 3
    # 待执行 全部0
    elif 0 in status_list and 2 not in status_list:
        status = 0
    # 完成 全部2
    elif 2 in status_list and 0 not in status_list:
        status = 2
    # 执行中 2和0都有
    else:
        status = 1

    return status
