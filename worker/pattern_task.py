from orm.models import PublishPatternTask
from orm.field_map import publish_pattern_task_status_map
from common.error import PublishError
from tornado.log import app_log


def get_action_tasks(action, application_type):
    action_map = {
        1: ['下载包到目标服务器', '执行发版'],  # 根据应用类型判断开启的服务
        2: [],  # 根据应用类型判断停止的服务
    }

    if action not in action_map:
        raise PublishError('Action %s not found' % action)

    tasks = action_map[action]
    if action == 1:
        if application_type == 1:  # web
            tasks.append('启动nginx')
        elif application_type == 2:  # mod
            tasks.append('启动dubbo')
        else:
            raise PublishError('Application type %s not found' % application_type)
    elif action == 2:
        if application_type == 1:  # web
            tasks.append('停止nginx')
        elif application_type == 2:  # mod
            tasks.append('停止dubbo')
        else:
            raise PublishError('Application type %s not found' % application_type)

    return tasks


def upgrade_pattern_task_status(ss, publish_pattern_task_id, ansible_status):
    app_log.debug('upgrade pattern task status, ansible_status is %s' % ansible_status)
    pattern_task = ss.query(PublishPatternTask).filter(
        PublishPatternTask.id == publish_pattern_task_id).with_for_update().one()
    pattern_task.status = publish_pattern_task_status_map[ansible_status]

    ss.flush()
    return pattern_task
