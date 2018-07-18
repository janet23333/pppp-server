from common.error import PublishError
from orm.field_map import publish_pattern_task_status_map
from orm.models import PublishPatternTask
from conf import settings


def get_action_tasks(action, application_type, application_name):
    apptype_flowtask_map = {
        'enable_flow': {
            1: ['启动nginx'],
            2: ['启动dubbo'],
            101: ['启动nginx', '启动dubbo'],
            102: ['启动dubbo', '启动nginx'],
        },
        'disable_flow': {
            1: ['停止nginx'],
            2: ['停止dubbo'],
            101: ['停止nginx', '停止dubbo'],
            102: ['停止dubbo', '停止nginx'],
        }
    }

    # 根据类型判断控制流量方式
    if application_type == 1:
        flow_type = 1
        if application_name in settings['special_mod_name']:
            flow_type = 101
    elif application_type == 2:
        flow_type = 2
        if application_name in settings['special_mod_name']:
            flow_type = 102
    else:
        raise PublishError('Application type not found: %s' % application_type)

    # 发版
    if action == 1:
        tasks = ['下载包到目标服务器', '备份日志']
        for t in apptype_flowtask_map['disable_flow'][flow_type]:
            tasks.append(t)
        tasks.extend(['停止应用', '改软链到新版本', '启动应用', '更新cmdb信息'])
        for t in apptype_flowtask_map['enable_flow'][flow_type]:
            tasks.append(t)

    # 断流量
    elif action == 2:
        tasks = []
        for t in apptype_flowtask_map['disable_flow'][flow_type]:
            tasks.append(t)

    # 回滚
    elif action == 11:
        tasks = ['备份日志']
        for t in apptype_flowtask_map['disable_flow'][flow_type]:
            tasks.append(t)
        tasks.extend(['停止应用', '改软链到回滚版本', '启动应用', '更新cmdb信息'])
        for t in apptype_flowtask_map['enable_flow'][flow_type]:
            tasks.append(t)

    # 接流量
    elif action == 12:
        tasks = []
        for t in apptype_flowtask_map['enable_flow'][flow_type]:
            tasks.append(t)

    # 断流量
    elif action == 14:
        tasks = []
        for t in apptype_flowtask_map['disable_flow'][flow_type]:
            tasks.append(t)
    else:
        raise PublishError('Action %s not found' % action)

    return tasks


def upgrade_pattern_task_status(ss, publish_pattern_task_id, ansible_status):
    pattern_task = ss.query(PublishPatternTask).filter(
        PublishPatternTask.id == publish_pattern_task_id).with_for_update().one()
    pattern_task.status = publish_pattern_task_status_map[ansible_status]

    ss.flush()
    return pattern_task
