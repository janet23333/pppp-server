import json

from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from tornado.web import HTTPError
from tornado.log import app_log

from celery_worker import app
from orm.db import session_scope
from orm.models import PublishPlan
from orm.models import PublishTask, AnsibleTaskResult
from worker.pattern import upgrade_pattern_status
from worker.pattern_host import upgrade_pattern_host_status
from worker.pattern_task import upgrade_pattern_task_status
from tasks.log_task import insert_host_log
from worker import run_task

logger = get_task_logger(__name__)

progress = {
    'get_package_failed': 5,
    'deploy_failed': 14,
    'nginx_start_failed': 24,
    'nginx_stop_failed': 34,
    'nginx_restart_failed': 74,
    'nginx_status_failed': 84,
    'nginx_configtest_failed': 94,
    'dubbo_enable_failed': 44,
    'dubbo_disable_failed': 54,
    'dubbo_status_failed': 64
}


def add_ansible_celery_result(ss, celery_task_id, result, is_failure=False):
    # TODO:
    # start/delta/end time  no result return
    if is_failure:
        #  运行出错
        status = "FAILED"
        ansible_task_result = AnsibleTaskResult()
        ansible_task_result.celery_task_id = celery_task_id
        ansible_task_result.stdout_lines = result
        ansible_task_result.status = status

        ss.add(ansible_task_result)
        ss.flush()

    success_result = result['success']
    failed_result = result["failed"]
    unreachable_result = result['unreachable']

    if success_result:
        status = "SUCCESS"
        result = success_result
    elif failed_result:
        status = "FAILED"
        result = failed_result
    elif unreachable_result:
        status = "UNREACHABLE"
        result = unreachable_result
    else:
        raise HTTPError(status_code=500, reason="ansible return empty result and result is {}".format(result))

    if len(result.keys()) > 1:
        raise HTTPError(status_code=500, reason="an ansible task with {} hosts".format(len(result.keys())))

    host = list(result.keys())[0]
    item = result[host]

    msg = []
    if 'stdout_lines' in item and item['stdout_lines']:
        msg.extend(item['stdout_lines'])
    if 'stderr_lines' in item and item['stderr_lines']:
        msg.extend(item['stderr_lines'])
    if 'msg' in item and item['msg']:
        msg.append(item['msg'])
    if "unreachable" in item and item["unreachable"]:
        msg.append('unreachhale: ' + str(item["unreachable"]))

    ansible_task_result = AnsibleTaskResult()
    ansible_task_result.celery_task_id = celery_task_id
    if status != "UNREACHABLE":
        ansible_task_result.rc = item['rc']
        ansible_task_result.cmd = item['cmd']
        ansible_task_result.delta_time = item['delta']
        ansible_task_result.start_time = item['start']
        ansible_task_result.end_time = item['end']

    ansible_task_result.host = host
    ansible_task_result.stdout_lines = json.dumps(msg)
    ansible_task_result.status = status

    ss.add(ansible_task_result)
    ss.flush()
    return ansible_task_result.status


@app.task
def success_callback(result, task_id, host, task_name, next_task_kwargs={}):

    argus = {"status": "SUCCESS", "result": json.dumps(result)}
    with session_scope() as ss:
        publish_task = ss.query(PublishTask).filter(PublishTask.celery_task_id == task_id).one_or_none()
        for k, v in argus.items():
            publish_task.__setattr__(k, v)
        ss.flush()

        pattern_task_id = publish_task.publish_pattern_task_id

        ansible_status = add_ansible_celery_result(ss, task_id, result)

        insert_host_log.delay(host, task_name, ansible_status)
        if pattern_task_id != 0:
            pattern_task = upgrade_pattern_task_status(ss, pattern_task_id, ansible_status)

            pattern_host_id = pattern_task.publish_pattern_host_id
            pattern_hosts = upgrade_pattern_host_status(ss, pattern_host_id)

            pattern_id = pattern_hosts[0].publish_pattern_id
            upgrade_pattern_status(ss, pattern_id)

        if ansible_status == 'SUCCESS':
            if next_task_kwargs:
                run_task.run_celery_task(session=ss, **next_task_kwargs)


@app.task
def failure_callback(uuid, host, task_name):

    insert_host_log.delay(host, task_name, 'FAILED')

    result = AsyncResult(uuid)

    err_msg = str(result.result)
    argus = {"status": "FAILED", "result": err_msg}

    with session_scope() as ss:
        publish_task = ss.query(PublishTask).filter(PublishTask.celery_task_id == uuid).one_or_none()
        for k, v in argus.items():
            publish_task.__setattr__(k, v)
        ss.flush()

        pattern_task_id = publish_task.publish_pattern_task_id

        ansible_status = add_ansible_celery_result(ss, uuid, err_msg, is_failure=True)

        if pattern_task_id != 0:
            pattern_task = upgrade_pattern_task_status(ss, pattern_task_id, ansible_status)

            pattern_host_id = pattern_task.publish_pattern_host_id
            pattern_hosts = upgrade_pattern_host_status(ss, pattern_host_id)

            pattern_id = pattern_hosts[0].publish_pattern_id
            upgrade_pattern_status(ss, pattern_id)


@app.task
def create_publish_plan_success_callback(publish_plan_id):
    # print('status is {}'.format(status))
    '''
    :param archive_package_list:  [{'target_version': target_version, 'application_name': application_name}]
    :param publish_plan_id: publish_plan_id
    :param  status： 发版任务创建状态 2： 成功，3： 失败
    :return:
    '''
    # print('in callback archive_package_list is{}'.format(archive_package_list))
    with session_scope() as ss:
        # 2: 创建完成 更新publish plan  状态
        ss.query(PublishPlan).filter(PublishPlan.id == publish_plan_id).update({'status': 2}, synchronize_session=False)


@app.task
def create_publish_plan_failed_callback(publish_plan_id, taskid=None):
    # print('status is {}'.format(status))
    '''
    :param archive_package_list:  [{'target_version': target_version, 'application_name': application_name}]
    :param publish_plan_id: publish_plan_id
    :param  status： 发版任务创建状态 2： 成功，3： 失败
    :return:
    '''
    # print('in callback archive_package_list is{}'.format(archive_package_list))
    with session_scope() as ss:
        # 2: 创建完成 更新publish plan  状态
        ss.query(PublishPlan).filter(PublishPlan.id == publish_plan_id).update({'status': 3}, synchronize_session=False)
    # 任务失败时，把错误信息 打到log
    if taskid:
        result = AsyncResult(taskid)
        err_msg = str(result.result)
        app_log.error(err_msg)
