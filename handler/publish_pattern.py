from handler.base import BaseHandler, HTTPError
from common.util import take_out_unrightful_arguments, pagination
from orm.models import PublishPattern, PublishApplication, PublishPatternHost
from common.authentication import validate_requests, validate_user_permission
from sqlalchemy import desc
from worker.pattern import get_publish_hosts
from orm.db import session_scope
from worker.commons import audit_log
from sqlalchemy.orm.exc import NoResultFound
from worker.run_task import run_celery_task


class PublishPatternHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('get')
    def get(self):
        res = []
        rightful_keys = (
            'id',
            'create_time',
            'update_time',
            'publish_plan_id',
            'step',
            'title',
            'note',
            'action',
            'status',
            'page',
            'page_size',
            'order_by',
            'desc',
        )
        uri_kwargs = take_out_unrightful_arguments(rightful_keys, self.url_arguments)
        page = int(uri_kwargs.pop("page", 1))
        page_size = int(uri_kwargs.pop("page_size", 15))
        order_by = uri_kwargs.pop("order_by", None)
        try:
            desc_ = int(uri_kwargs.pop('desc', 0))
        except ValueError:
            desc_ = 0

        with session_scope() as ss:
            q = ss.query(PublishPattern).filter_by(**uri_kwargs)
            if order_by is not None:
                if desc_:
                    order_by = desc(order_by)
                q = q.order_by(order_by)
            total_count = q.count()
            db_res = pagination(q, page, page_size)

            for pattern in db_res:
                r = pattern.to_dict()
                r['publish_application_hosts'] = get_publish_hosts(pattern)

                res.append(r)

            self.render_json_response(code=200, msg='ok', total_count=total_count, res=res)

    @validate_requests
    @validate_user_permission('put')
    def put(self):
        res = {}
        rightful_keys = (
            'id',
            'step',
            'title',
            'note',
            'action',
            'status',
        )
        body_kwargs = take_out_unrightful_arguments(rightful_keys, self.body_arguments)

        id_ = body_kwargs.pop('id', None)
        if id_ is None:
            raise HTTPError(status_code=400, reason='Missing argument "id"')

        with session_scope() as ss:
            q = ss.query(PublishPattern).filter_by(id=id_)
            q.update(body_kwargs)

            db_res = q.one_or_none()
            if db_res is not None:
                res = db_res.to_dict()

        audit_log(self, description='更新发版步骤', resource_type=4, resource_id=id_)
        self.render_json_response(code=200, res=res)


class PatternAction(BaseHandler):
    @validate_requests
    @validate_user_permission('post')
    def post(self):
        """
        执行pattern
        request params:
        {
            "pattern_id": pattern_id
        }
        """
        pattern_id = self.body_arguments.pop("pattern_id", None)
        if pattern_id is None:
            raise HTTPError(status_code=400, reason="Missing argument 'pattern_id'")

        app_id_map = {}
        ready_host_tasks = {}

        with session_scope() as ss:
            try:
                # check pattern status
                pattern_status = ss.query(PublishPattern.status).filter_by(id=pattern_id).with_for_update().one()[0]
                if pattern_status == 1:
                    raise HTTPError(status_code=400, reason="请求步骤正在执行中")
            except NoResultFound:
                raise HTTPError(status_code=400, reason="Find pattern id not found: %s" % pattern_id)

            pattern_hosts = ss.query(PublishPatternHost).filter(
                PublishPatternHost.publish_pattern_id == pattern_id).all()
            pattern_hosts = [t.to_dict() for t in pattern_hosts]

            for pattern_host in pattern_hosts:
                tasks = []
                publish_host = pattern_host['publish_host']

                try:
                    app_detail = app_id_map.setdefault(
                        publish_host['publish_application_id'],
                        ss.query(PublishApplication).filter_by(
                            id=publish_host['publish_application_id']).one().to_dict())
                except NoResultFound:
                    raise HTTPError(
                        status_code=400,
                        reason="找不到publish_application_id: %s" % publish_host['publish_application_id'])

                for task in pattern_host['publish_pattern_tasks']:
                    task_kwargs = None

                    # 只执行状态是 0：待执行 3：失败 的任务
                    if task['status'] not in (0, 3):
                        continue

                    task_name = task['task_name']
                    if task_name == "下载包到目标服务器":
                        task_kwargs = {
                            "publish_host_id_list": [publish_host['id']],
                            "task_name": task_name,
                            "pattern_id": pattern_id,
                            "version": app_detail['target_version'],
                            "project_name": app_detail['application_name'],
                        }
                    elif task_name == "执行发版":
                        task_kwargs = {
                            "publish_host_id_list": [publish_host['id']],
                            "task_name": task_name,
                            "pattern_id": pattern_id,
                            "version": app_detail['target_version'],
                            "project_name": app_detail['application_name'],
                        }
                    elif task_name == "启动dubbo":
                        task_kwargs = {
                            "publish_host_id_list": [publish_host['id']],
                            "task_name": task_name,
                            "pattern_id": pattern_id,
                        }
                    elif task_name == "停止dubbo":
                        task_kwargs = {
                            "publish_host_id_list": [publish_host['id']],
                            "task_name": task_name,
                            "pattern_id": pattern_id,
                        }
                    elif task_name == "启动nginx":
                        task_kwargs = {
                            "publish_host_id_list": [publish_host['id']],
                            "task_name": task_name,
                            "pattern_id": pattern_id,
                        }
                    elif task_name == "停止nginx":
                        task_kwargs = {
                            "publish_host_id_list": [publish_host['id']],
                            "task_name": task_name,
                            "pattern_id": pattern_id,
                        }
                    if task_kwargs is None:
                        raise HTTPError(status_code=400, reason="没有匹配的任务：%s" % task_name)

                    tasks.append(task_kwargs)
                if tasks:
                    host_tasks = ready_host_tasks.setdefault(publish_host['host_name'], [])
                    host_tasks.extend(tasks)

            # 链式执行任务
            for host_tasks in ready_host_tasks.values():
                is_first = True

                for task in reversed(host_tasks):
                    if is_first:
                        is_first = False
                        host_action = task
                        continue

                    task['next_task_kwargs'] = host_action.copy()
                    host_action = task

                run_celery_task(session=ss, **host_action)

        audit_log(handler=self, description="执行发版步骤", resource_type=4, resource_id=pattern_id)
        self.render_json_response(code=200, res=ready_host_tasks)
