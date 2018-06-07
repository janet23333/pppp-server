from celery import uuid
from tornado.web import HTTPError

from orm.models import PublishHost, PublishPatternTask, PublishPatternHost
from tasks import callback
from tasks.log_task import insert_host_log
from worker.pattern import upgrade_pattern_status
from worker.pattern_host import upgrade_pattern_host_status
from worker.pattern_task import upgrade_pattern_task_status
from worker.publish_task import add_publish_task
from tasks import task_name_to_task_obj
from sqlalchemy.orm.exc import NoResultFound


def run_celery_task(session, publish_host_id_list, task_name, pattern_id=None, next_task_kwargs={}, **kwargs):
    """
    执行celery task并记录到数据库
        :param session: (<sqlalchemy.orm.session.Session>) database session
        :param publish_host_id_list: (list) publish_host_id list
        :param task_name: (string) 任务名字
        :param pattern_id: (int) pattern id
        :param next_task_kwargs: success callback调用的task和参数
        :param kwargs: 调用celery task的时传入的参数
    """
    status = 'STARTED'
    query = session.query(PublishHost.id, PublishHost.host_ip, PublishHost.host_name).filter(
        PublishHost.id.in_(publish_host_id_list))
    res = query.all()
    host_and_id_list = [{"host_ip": item[1], "publish_host_id": item[0], 'host_name': item[2]} for item in res]

    if not host_and_id_list:
        raise HTTPError(
            status_code=400, reason="Not Found host with publish_host_id of {}".format(publish_host_id_list))

    try:
        action = task_name_to_task_obj[task_name]
    except KeyError:
        raise HTTPError(status_code=400, reason="Find task obj not found: %s" % task_name)

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
                    PublishPatternTask.task_name == task_name
                ).one_or_none()[0]
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

        insert_host_log.delay(host, task_name, status)
        action.apply_async(
            kwargs=kwargs_,
            task_id=task_id,
            link=callback.success_callback.s(task_id, host, task_name, next_task_kwargs=next_task_kwargs),
            link_error=callback.failure_callback.si(task_id, host, task_name))
        host.update({'task_id': task_id, 'task_name': task_name, 'publish_host_id': publish_host_id})
    return host_and_id_list
