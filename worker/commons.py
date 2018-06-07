from common.sdk.cmdb_sdk import CmdbSdk
from conf import settings
from tasks.log_task import insert_audit_log
from tornado.log import app_log

url = settings['cmdb_server']['url']
token = settings['cmdb_server']['token']
CMDB = CmdbSdk(host=url, token=token)

save_path = settings['inventory']


def audit_log(handler, description, resource_type, resource_id, visible=True):
    if visible:
        visible_ = 1
    else:
        visible_ = 0

    insert_audit_log.delay(
        user_id=handler.user['id'],
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        visible=visible_,
        method=handler.request.method,
        path=handler.request.path,
        fullpath=handler.request.protocol + '://' + handler.request.host + handler.request.uri,
        body=handler.request.body)


def run_ansible(cmdstr, host, become=False, become_user=None, module='shell'):
    from common.sdk.ansible import exec_ansible
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
    res = CMDB.get('host', **kwargus)
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
    app_log.debug('check status: %s' % str(status_list))

    # 失败
    if 3 in status_list:
        status = 3
    # 执行中
    elif 1 in status_list:
        status = 1
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
