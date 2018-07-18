from sqlalchemy.sql import func
from sqlalchemy.orm.exc import NoResultFound
from tornado.web import HTTPError

from orm.db import session_scope

from orm.models import PublishPattern, PublishPatternHost, PublishPlan
from orm.models import PublishHost, PublishApplication
from orm.models import PublishPatternTask
from worker.commons import get_cmdb_host_application
from worker.run_task import get_action_tasks
from common.error import PublishError
from worker.run_task import run_celery_task


def get_host_by_publish_plan_id(publish_plan_id):
    host_application_list_res = list()
    host_application_dict = dict()
    with session_scope() as ss:
        query = ss.query(PublishHost, PublishApplication).join(
            PublishApplication, PublishApplication.id == PublishHost.publish_application_id).join(
            PublishPatternHost, PublishPatternHost.publish_host_id == PublishHost.id).join(
            PublishPattern, PublishPattern.id == PublishPatternHost.publish_pattern_id).join(
            PublishPlan, PublishPlan.id == PublishPattern.publish_plan_id
        )

        # PublishPattern.status 2: 完成 3：失败
        # PublishPattern.action 1: 发布 2: 停服务 3: 提示
        query = query.filter(PublishPattern.publish_plan_id == publish_plan_id,
                             PublishPlan.status.in_([4, 5, 8]),
                             PublishPattern.status.in_([2, 3]),
                             PublishPattern.action.in_([1, 2]))

        db_res = query.all()

        for ii in db_res:
            host, application = ii
            if host.rollback_version:
                # 只有有rollback_version 的才可以进行回滚， 新应用无法进行回滚
                _key = '{}_{}'.format(host.id, host.publish_application_id)
                host_application_list = host_application_dict.setdefault(_key, [])
                host_application_list.append({
                    'publish_host_id': host.id,
                    'host_ip': host.host_ip,
                    'host_name': host.host_name,
                    'rollback_version': host.rollback_version,
                    'host_flag': host.host_flag,
                    'application_name': application.application_name,
                    'target_version': application.target_version,
                    'application_type': application.application_type,
                })

    for _list in list(host_application_dict.values()):
        host_application_list_res.extend(_list)
    return host_application_list_res


def get_current_version_from_cmdb(host_name_list, application_name_list):
    hostname_version_dict = dict()
    host_name_str = (','.join(host_name_list))
    app_name_str = (','.join(application_name_list))
    kwargus = dict(host_name=host_name_str, application_name=app_name_str)
    res = get_cmdb_host_application(kwargus)
    for uu in res:
        _key = '{}_{}'.format(uu['hostname'], uu['application_name'])
        hostname_version_dict.update({_key: uu['version']})
    return hostname_version_dict


def divide_host_by_version(host_application_list):
    """
    根据新旧版本 对 主机分类
    :param host_application_list:
    :return:
    """
    host_name_list = [ii['host_name'] for ii in host_application_list]
    application_name_list = [ii['application_name'] for ii in host_application_list]

    # 从cmdb 获取版本信息
    hostname_version_dict = get_current_version_from_cmdb(host_name_list, application_name_list)

    old_version_host_list = list()
    new_version_host_list = list()
    for host_app in host_application_list:
        rollback_version = host_app['rollback_version']
        host_name = host_app['host_name']
        app_name = host_app['application_name']
        _key = '{}_{}'.format(host_name, app_name)
        if _key in hostname_version_dict and hostname_version_dict[_key] == rollback_version:
            old_version_host_list.append(host_app)
        else:
            new_version_host_list.append(host_app)
    return [old_version_host_list, new_version_host_list]


def host_application_list_to_dict(host_application_list):
    '''
    以application 作为key
    :param host_application_list:
    :return:
    format: {application_name:[host_application]}
    '''
    host_application_dict = dict()
    for host_app in host_application_list:
        application_name = host_app['application_name']
        host_application_dict.setdefault(application_name, []).append(host_app)

    return host_application_dict


def check_rollback_status(host_application_list):
    '''
    检测此时是否回滚了一半
    :return:  True: 已回滚一半及以上
              False: 未回滚到一半
    '''
    host_name_list = [ii['host_name'] for ii in host_application_list]
    application_name_list = [ii['application_name'] for ii in host_application_list]

    # 从cmdb 获取版本信息
    hostname_version_dict = get_current_version_from_cmdb(host_name_list, application_name_list)

    #  数组转换为 dict
    host_application_dict = host_application_list_to_dict(host_application_list)

    # 记录各个application的 新旧版本的主机数量
    app_version_num = dict()
    for (app_name, host_list) in host_application_dict.items():
        for host in host_list:
            host_name = host['host_name']
            rollback_version = host['rollback_version']
            _key = '{}_{}'.format(host_name, app_name)
            num_dict = app_version_num.setdefault(app_name, {})
            #  主机类型'gray': 3 'master': 1, 'slave': 2,
            if host['host_flag'] == 3:
                #  灰度机数量
                num_dict['gray_host_num'] = num_dict.setdefault(
                    'gray_host_num', 0) + 1
            elif hostname_version_dict[_key] == rollback_version:
                num_dict['old_version_num'] = num_dict.setdefault(
                    'old_version_num', 0) + 1
            else:
                num_dict['new_version_num'] = num_dict.setdefault(
                    'new_version_num', 0) + 1

    app_version_check_dist = {}
    for (app_name, host_list) in host_application_dict.items():
        old_version_num = app_version_num[app_name].get('old_version_num', 0)
        new_version_num = app_version_num[app_name].get('new_version_num', 0)
        gray_host_num = app_version_num[app_name].get('gray_host_num', 0)
        # 是否已回滚了一半 及以上
        if old_version_num < new_version_num:
            not_half_app = app_version_check_dist.setdefault('lt_half_rollback', [])
            not_half_app.append(app_name)
        elif (gray_host_num + old_version_num) == len(host_list):
            full_rollback_app = app_version_check_dist.setdefault('full_rollback', [])
            full_rollback_app.append(app_name)
        else:
            half_app = app_version_check_dist.setdefault('half_rollback', [])
            half_app.append(app_name)

    return app_version_check_dist


def create_publish_pattern(publish_pattern_list):
    pattern_id_list = list()
    with session_scope() as ss:
        for publish_pattern_kwargus in publish_pattern_list:
            host_app_list = publish_pattern_kwargus.pop('host_app_list', [])
            # 创建 publish pattern
            pattern = PublishPattern(**publish_pattern_kwargus)
            ss.add(pattern)
            ss.flush()
            pattern_id = pattern.id
            pattern_id_list.append(pattern_id)

            for publish_host_kwargs in host_app_list:
                #  action:13 回滚提示，进不来此处，host_app_list  为空
                publish_host_id = publish_host_kwargs['publish_host_id']

                #  创建 PublishPatternHost
                pattern_host = PublishPatternHost()
                pattern_host.publish_host_id = publish_host_id
                pattern_host.publish_pattern_id = pattern_id
                ss.add(pattern_host)
                ss.flush()

                # 创建 publish_pattern_task
                pattern_host_id = pattern_host.id
                try:
                    tasks = get_action_tasks(
                        action=publish_pattern_kwargus['action'],
                        application_type=publish_host_kwargs['application_type'],
                        application_name=publish_host_kwargs['application_name']
                    )
                except PublishError as e:
                    raise HTTPError(status_code=400, reason=str(e))
                ss.add_all(
                    [PublishPatternTask(publish_pattern_host_id=pattern_host_id, task_name=task) for task in tasks])
                ss.flush()
    return pattern_id_list


def stop_new_version_host_flow(step, publish_plan_id, host_application_list, new_version_host_list):
    '''
    进行回滚到一半时 ，先把新版本服务的流量摘掉
    :param step:
    :param publish_plan_id:
    :param host_application_list:
    :param new_version_host_list:
    :return:
    '''

    app_version_check_dist = check_rollback_status(host_application_list)
    half_app_name_list = app_version_check_dist.get('half_rollback', [])
    lt_half_rollback_app_name_list = app_version_check_dist.get('lt_half_rollback', [])

    if lt_half_rollback_app_name_list or not half_app_name_list:
        # 还有应用没回滚到一半 或者已全部回滚
        return []

    half_new_version_host_list = list(
        filter(lambda x: x['application_name'] in half_app_name_list, new_version_host_list))

    # 新版本 摘流量
    patterns = [
        {
            "action": 14,
            "title": "摘新版本服务流量",
            "step": step,
            'publish_plan_id': publish_plan_id,
            'host_app_list': half_new_version_host_list
        },
        {
            "action": 19,
            "title": "已回滚到一半,请确认",
            "step": step + 1,
            'publish_plan_id': publish_plan_id,
            'host_app_list': []
        },
    ]

    return patterns


def generate_rollback_steps(publish_plan_id, host_application_list):
    # 旧版本 新版本主机分类
    old_version_host_list, new_version_host_list = divide_host_by_version(host_application_list)

    with session_scope() as ss:
        step = ss.query(func.max(PublishPattern.step)).filter_by(publish_plan_id=publish_plan_id).one()[0]

    publish_pattern_list = []
    if old_version_host_list:
        step = step + 1
        # 旧版本 启动服务
        publish_pattern_list.append(
            {
                "action": 12,
                "title": "接旧版本服务流量",
                "step": step,
                'publish_plan_id': publish_plan_id,
                'host_app_list': old_version_host_list
            }
        )
        if new_version_host_list:
            step = step + 1
            patterns = stop_new_version_host_flow(step, publish_plan_id, host_application_list, new_version_host_list)
            if patterns:
                publish_pattern_list.extend(patterns)
                step = step + 1
            else:
                step = step - 1

    web_host_app_list = list()
    mod_host_app_list = list()

    # 先按 web /mod 区分应用 # application_type: 1 web 2 mod
    for host_app in new_version_host_list:
        if host_app['application_type'] == 1:
            web_host_app_list.append(host_app)
        elif host_app['application_type'] == 2:
            mod_host_app_list.append(host_app)

    # 主机标识 host_flag 1:master 2:slave 3:gray
    web_host_app_master_list = list(filter(lambda x: x['host_flag'] == 1, web_host_app_list))
    mod_host_app_master_list = list(filter(lambda x: x['host_flag'] == 1, mod_host_app_list))
    all_host_app_slave_list = list(filter(lambda x: x['host_flag'] == 2, new_version_host_list))
    all_host_app_gray_list = list(filter(lambda x: x['host_flag'] == 3, new_version_host_list))

    if web_host_app_master_list:
        step = step + 1
        publish_pattern_list.append(
            {
                "action": 11,
                "title": "执行回滚web:master",
                "step": step,
                'publish_plan_id': publish_plan_id,
                'host_app_list': web_host_app_master_list
            }
        )
    if mod_host_app_master_list:
        step = step + 1
        publish_pattern_list.append(
            {
                "action": 11,
                "title": "执行回滚mod:master",
                "step": step,
                'publish_plan_id': publish_plan_id,
                'host_app_list': mod_host_app_master_list
            }
        )

    if (web_host_app_master_list or mod_host_app_master_list) and (all_host_app_slave_list or all_host_app_gray_list):
        # 是否回滚到了一半， 中途停顿
        # 新版本 摘流量
        all_host_app_slave_gray_list = []
        title = []
        if all_host_app_slave_list:
            all_host_app_slave_gray_list.extend(all_host_app_slave_list)
            title.append('slave')
        if all_host_app_gray_list:
            all_host_app_slave_gray_list.extend(all_host_app_gray_list)
            title.append('gray')
        step = step + 1
        patterns = [
            {
                "action": 14,
                "title": "摘新版本服务流量",
                "step": step,
                'publish_plan_id': publish_plan_id,
                'host_app_list': all_host_app_slave_gray_list
            },
            {
                "action": 19,
                "title": "已回滚到一半,请确认",
                "step": step + 1,
                'publish_plan_id': publish_plan_id,
                'host_app_list': []
            },
        ]
        publish_pattern_list.extend(patterns)
        step = step + 1

    if all_host_app_slave_list or all_host_app_gray_list:
        all_host_app_slave_gray_list = []
        title = []
        if all_host_app_slave_list:
            all_host_app_slave_gray_list.extend(all_host_app_slave_list)
            title.append('slave')
        if all_host_app_gray_list:
            all_host_app_slave_gray_list.extend(all_host_app_gray_list)
            title.append('gray')
        step = step + 1
        publish_pattern_list.append({
            "action": 11,
            "title": "执行回滚: {}".format('+'.join(title)),
            "step": step,
            'publish_plan_id': publish_plan_id,
            'host_app_list': all_host_app_slave_gray_list
        })

    step = step + 1
    publish_pattern_list.append({
        "action": 13,
        "title": "QA 验证回滚",
        "step": step,
        'publish_plan_id': publish_plan_id,
        'host_app_list': []
    })

    # 生成回滚步骤并写入数据库
    pattern_id_list = create_publish_pattern(publish_pattern_list)
    return pattern_id_list


def get_next_kwargus(_dict):
    if "next_task_kwargs" in _dict:
        a = _dict["next_task_kwargs"][0]
        return get_next_kwargus(a)
    else:
        return _dict


def handle_pattern_ready_host_task(ss, pattern_id):
    '''
     获取每一步的 host task
    :param ss:
    :param pattern_hosts:
    :param pattern_id:
    :return: ready_host_tasks： { hostname: [tasks]}
    '''
    ready_host_tasks = {}
    pattern_hosts = ss.query(PublishPatternHost).filter(
        PublishPatternHost.publish_pattern_id == pattern_id).all()
    pattern_hosts = [t.to_dict() for t in pattern_hosts]
    for pattern_host in pattern_hosts:
        tasks = []
        publish_host = pattern_host['publish_host']

        for task in pattern_host['publish_pattern_tasks']:
            # 主机中有任务在执行，直接跳出
            if task['status'] == 1:
                break
            # 只执行状态是 0：待执行 3：失败 的任务
            if task['status'] not in (0, 3):
                continue

            task_name = task['task_name']
            task_kwargs = {
                "publish_host_id_list": [publish_host['id']],
                "task_name": task_name,
                "pattern_id": pattern_id
            }
            tasks.append(task_kwargs)
        if tasks:
            host_tasks = ready_host_tasks.setdefault(publish_host['host_name'], [])
            host_tasks.extend(tasks)
    return ready_host_tasks


def link_pattern_tasks(pattern_ready_hot_task_list):
    """
     把每一步的tasks 串起来
    :param pattern_ready_hot_task_list:
    :return:
    """
    pattern_is_first = True
    for pattern_host_task_dict in reversed(pattern_ready_hot_task_list):
        pattern_id = list(pattern_host_task_dict.values())[0][0]["pattern_id"]
        # 链式执行任务
        pattern_host_action_list = []
        #  一个步骤里面 ,循环多台主机
        for host_tasks in pattern_host_task_dict.values():
            # host_tasks 单台主机接受的task
            is_first = True
            for task in reversed(host_tasks):
                if is_first:
                    is_first = False
                    host_action = task
                    continue
                task['next_task_kwargs'] = [host_action.copy()]
                host_action = task

            # 一个步骤里并行执行的task(按主机来划分)
            pattern_host_action_list.append(host_action)

        # 执行下一个pattern 前先检测上一步的执行状态
        check_pattern_status_task = [
            {'publish_host_id_list': [],
             'task_name': '检测上一步执行状态',
             'pattern_id': '',
             'next_task_kwargs': pattern_host_action_list
             }
        ]
        if pattern_is_first:
            pattern_is_first = False
            pattern_action = check_pattern_status_task
            continue

        _dict = get_next_kwargus(pattern_host_action_list[0])
        pattern_action[0].update({'pattern_id': pattern_id})
        _dict['next_task_kwargs'] = pattern_action
        pattern_action = check_pattern_status_task
    return pattern_ready_hot_task_list


def run_rollback_pattern(pattern_id_list):
    pattern_ready_hot_task_list = []

    with session_scope() as ss:
        for pattern_id in pattern_id_list:
            try:
                # check pattern status
                pattern_status = ss.query(PublishPattern.status).filter_by(id=pattern_id).with_for_update().one()[0]
                if pattern_status == 1:
                    raise HTTPError(status_code=400, reason="请求步骤正在执行中")
            except NoResultFound:
                raise HTTPError(status_code=400, reason="Find pattern id not found: %s" % pattern_id)
            # 获取每一步的 host task
            ready_host_tasks = handle_pattern_ready_host_task(ss, pattern_id)
            if ready_host_tasks:
                pattern_ready_hot_task_list.append(ready_host_tasks)
            else:
                # TODO
                ##步骤没有task需要执行
                # 进一步处理
                pass

        # link pattern task
        pattern_ready_hot_task_list = link_pattern_tasks(pattern_ready_hot_task_list)

        ready_run_tasks = []
        if pattern_ready_hot_task_list:
            for hostname, host_tasks in pattern_ready_hot_task_list[0].items():
                task = host_tasks[0]
                ready_run_tasks.append(task)
                run_celery_task(session=ss, **task)

    return ready_run_tasks


def get_retry_rollback_pattern_ids(publish_plan_id):
    """
    获取 未完成的 回滚步骤id
    :param publish_plan_id:
    :return:
    """
    with session_scope() as ss:
        patterns = ss.query(PublishPattern).filter(PublishPattern.publish_plan_id == publish_plan_id,
                                                   PublishPattern.action.in_([11, 12, 14, 19]),
                                                   PublishPattern.status != 2
                                                   ).order_by(
            PublishPattern.step).all()
        retry_pattern_id_list = []
        for pattern in patterns:
            #  有停顿，不再往下
            if pattern.action == 19 and retry_pattern_id_list:
                break
            # status 任务状态 0: 待执行 1:执行中 2：完成 3：失败
            if pattern.status == 1:
                raise HTTPError(status_code=400,
                                reason=' {} with publish_plan_id {} and publish_pattern_id {} is running'.format(
                                    pattern.title, publish_plan_id, pattern.id))
            elif pattern.status == 2:
                continue
            else:
                retry_pattern_id_list.append(pattern.id)
    return retry_pattern_id_list
