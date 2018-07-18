from celery import uuid
from sqlalchemy.orm.exc import NoResultFound
from tornado.web import HTTPError
from conf import settings
from orm.field_map import application_type_id_map
from orm.models import PublishHost, PublishPatternTask, PublishPatternHost, PublishApplication, PublishScript
from worker.pattern import upgrade_pattern_status
from worker.pattern_host import upgrade_pattern_host_status
from worker.pattern_task import upgrade_pattern_task_status
from worker.publish_task import add_publish_task
from worker.publish_plan import upgrade_plan_finish
from common.error import PublishError


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
    elif action == 2 or action == 14:
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
    else:
        raise PublishError('Action %s not found' % action)

    return tasks


def run_chain_tasks(session, ready_host_tasks, upgrade_plan_finish=False, plan_id=0):
    """
    链式执行任务
        :param session: (<sqlalchemy.orm.session.Session>) database session
        :param ready_host_tasks: (list or tuple) 要执行的任务，多维数组，代表多个主机的任务，ex: [[task, task], [task, task]]
        :param upgrade_plan_finish=False: (bool) 是否最后更新plan完成状态
        :param plan_id=0: (int) 更新状态的plan_id
    """

    res = []
    max_host_index = len(ready_host_tasks)
    len_host_index = 0
    for host_tasks in ready_host_tasks:
        is_first = True
        len_host_index += 1

        for task in reversed(host_tasks):
            if is_first:
                is_first = False

                if upgrade_plan_finish and len_host_index == max_host_index:
                    task['next_task_kwargs'] = [{
                        'task_name': 'upgrade_plan_finish',
                        'plan_id': plan_id,
                    }]
                host_action = task
                continue

            task['next_task_kwargs'] = [host_action.copy()]
            host_action = task

        r = run_celery_task(session=session, **host_action)
        res.append(r)
    return res


def run_celery_task(session, task_name, **kwargs):
    """
    执行celery task并记录到数据库
        :param session: (<sqlalchemy.orm.session.Session>) database session
        :param task_name: (string) 任务名字
        :param kwargs: 调用celery task的时传入的参数
    """
    print(task_name, kwargs)
    if task_name == '检测上一步执行状态':
        return run_status_task(session, task_name, **kwargs)

    elif task_name == 'upgrade_plan_finish':
        return upgrade_plan_finish(session, kwargs['plan_id'])

    elif task_name in ('启动dubbo', '停止dubbo', '查询dubbo状态'):
        return run_dubbo_task(session=session, task_name=task_name, **kwargs)

    else:
        return run_ansible_task(session=session, task_name=task_name, **kwargs)


def run_dubbo_task(session, publish_host_id_list, task_name, pattern_id=None, **kwargs):
    from tasks import dubbo
    if task_name == '启动dubbo':
        action = dubbo.enable
    elif task_name == '停止dubbo':
        action = dubbo.disable
    else:
        action = dubbo.status

    status = 'STARTED'

    query = session.query(PublishHost.id, PublishHost.host_ip, PublishHost.host_name).filter(
        PublishHost.id.in_(publish_host_id_list))
    res = query.all()
    host_and_id_list = [{"host_ip": item[1], "publish_host_id": item[0], 'host_name': item[2]} for item in res]

    if not host_and_id_list:
        raise HTTPError(
            status_code=400, reason="Not Found host with publish_host_id of {}".format(publish_host_id_list))

    for host in host_and_id_list:
        kwargs_ = kwargs.copy()
        publish_host_id = host['publish_host_id']
        kwargs_['host'] = host['host_ip']

        task_id = uuid()

        # 获取pattern task id
        pattern_task_id = 0
        if pattern_id is not None:
            try:
                pattern_task_id = session.query(PublishPatternTask.id).join(
                    PublishPatternHost, PublishPatternHost.id == PublishPatternTask.publish_pattern_host_id).filter(
                    PublishPatternHost.publish_host_id == publish_host_id,
                    PublishPatternHost.publish_pattern_id == pattern_id,
                    PublishPatternTask.task_name == task_name).one()[0]
            except NoResultFound:
                raise HTTPError(status_code=400, reason='Pattern task not found.')

        add_publish_task(
            session=session,
            task_id=task_id,
            task_name=task_name,
            publish_host_id=publish_host_id,
            pattern_task_id=pattern_task_id,
            status=status)

        # 更新状态
        if pattern_id is not None:
            pattern_task = upgrade_pattern_task_status(session, pattern_task_id, status)
            upgrade_pattern_host_status(session, pattern_task.publish_pattern_host_id)
            upgrade_pattern_status(session, pattern_id)

        if kwargs_.get('project_name') is None:
            kwargs_['project_name'] = _get_application_name(session, publish_host_id)

        action.apply_async(kwargs=kwargs_, task_id=task_id)

        host.update({'task_id': task_id, 'task_name': task_name, 'publish_host_id': publish_host_id})

    return host_and_id_list


def run_status_task(session, task_name, pattern_id=None, **kwargs):
    from tasks import check_pattern_status
    action = check_pattern_status.check_pattern_status
    status = 'STARTED'
    task_id = uuid()
    publish_host_id = 0
    pattern_task_id = 0
    add_publish_task(
        session=session,
        task_id=task_id,
        task_name=task_name,
        publish_host_id=publish_host_id,
        pattern_task_id=pattern_task_id,
        status=status)
    kwargs_ = kwargs.copy()
    kwargs_.pop('publish_host_id_list', None)
    kwargs_['pattern_id'] = pattern_id
    action.apply_async(kwargs=kwargs_, task_id=task_id)
    return [{'task_id': task_id}]


def run_ansible_task(session, publish_host_id_list, task_name, pattern_id=None, **kwargs):
    from tasks.ansible_script import run as ansible_script_runner

    # TODO: 改成可自定义
    script = session.query(PublishScript).filter_by(alias=task_name).one_or_none()
    if script is None:
        raise HTTPError(status_code=400, reason="没有匹配的任务: %s" % task_name)
    script = script.to_dict()

    status = 'STARTED'

    query = session.query(PublishHost.id, PublishHost.host_ip, PublishHost.host_name).filter(
        PublishHost.id.in_(publish_host_id_list))
    res = query.all()
    host_and_id_list = [{"host_ip": item[1], "publish_host_id": item[0], 'host_name': item[2]} for item in res]

    if not host_and_id_list:
        raise HTTPError(
            status_code=400, reason="Not Found host with publish_host_id of {}".format(publish_host_id_list))

    for host in host_and_id_list:
        kwargs_ = kwargs.copy()
        publish_host_id = host['publish_host_id']

        task_id = uuid()

        # 获取pattern task id
        pattern_task_id = 0
        if pattern_id is not None:
            try:
                pattern_task_id = session.query(PublishPatternTask.id).join(
                    PublishPatternHost, PublishPatternHost.id == PublishPatternTask.publish_pattern_host_id).filter(
                    PublishPatternHost.publish_host_id == publish_host_id,
                    PublishPatternHost.publish_pattern_id == pattern_id,
                    PublishPatternTask.task_name == task_name).one()[0]
            except NoResultFound:
                raise HTTPError(status_code=400, reason='Pattern task not found.')

        add_publish_task(
            session=session,
            task_id=task_id,
            task_name=task_name,
            publish_host_id=publish_host_id,
            pattern_task_id=pattern_task_id,
            status=status)

        # 更新状态
        if pattern_id is not None:
            pattern_task = upgrade_pattern_task_status(session, pattern_task_id, status)
            upgrade_pattern_host_status(session, pattern_task.publish_pattern_host_id)
            upgrade_pattern_status(session, pattern_id)

        args = [host['host_ip'], script['name'], script['become_user']]
        args.extend([_get_script_argument(session, publish_host_id, a) for a in script['arguments']])

        ansible_script_runner.apply_async(kwargs=kwargs_, args=args, task_id=task_id)

        host.update({'task_id': task_id, 'task_name': task_name, 'publish_host_id': publish_host_id})

    return host_and_id_list


def _get_script_argument(session, publish_host_id, variable):
    if not (variable.startswith('{') or variable.endswith('}')):
        return variable

    var_to_method_map = {
        '{application_name}': _get_application_name,
        '{application_type}': _get_application_type,
        '{deploy_real_path}': _get_deploy_real_path,
        '{target_version}': _get_target_version,
        '{rollback_version}': _get_rollback_version,
        '{package_source_url}': _get_package_source_url,
    }

    method = var_to_method_map.get(variable)
    if method is None:
        raise HTTPError(status_code=400, reason="Not support argument %s" % variable)

    res = method(session, publish_host_id)
    return res


def _get_application_name(session, publish_host_id, *args):
    app = session.query(PublishApplication.application_name).join(
        PublishHost, PublishApplication.id == PublishHost.publish_application_id).filter(
        PublishHost.id == publish_host_id).one_or_none()

    if app is None:
        raise HTTPError(status_code=400, reason="Not found application with publish_host_id of %s" % publish_host_id)
    return app[0]


def _get_application_type(session, publish_host_id, *args):
    app = session.query(PublishApplication.application_type).join(
        PublishHost, PublishApplication.id == PublishHost.publish_application_id).filter(
        PublishHost.id == publish_host_id).one_or_none()

    if app is None:
        raise HTTPError(status_code=400, reason="Not found application with publish_host_id of %s" % publish_host_id)
    return application_type_id_map[app[0]]


def _get_deploy_real_path(session, publish_host_id, *args):
    app = session.query(PublishApplication.deploy_real_path).join(
        PublishHost, PublishApplication.id == PublishHost.publish_application_id).filter(
        PublishHost.id == publish_host_id).one_or_none()

    if app is None:
        raise HTTPError(status_code=400, reason="Not found application with publish_host_id of %s" % publish_host_id)
    return app[0]


def _get_target_version(session, publish_host_id, *args):
    app = session.query(PublishApplication.target_version).join(
        PublishHost, PublishApplication.id == PublishHost.publish_application_id).filter(
        PublishHost.id == publish_host_id).one_or_none()

    if app is None:
        raise HTTPError(status_code=400, reason="Not found application with publish_host_id of %s" % publish_host_id)
    return app[0]


def _get_rollback_version(session, publish_host_id, *args):
    host = session.query(PublishHost.rollback_version).filter_by(id=publish_host_id).one_or_none()

    if host is None:
        raise HTTPError(status_code=400, reason="Not found host with publish_host_id of %s" % publish_host_id)
    return host[0]


def _get_package_source_url(*args):
    return settings['package_source_url']
