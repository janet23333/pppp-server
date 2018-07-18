from sqlalchemy import desc, func
from sqlalchemy.orm.exc import NoResultFound
from common.authentication import validate_requests, validate_user_permission
from common.util import take_out_unrightful_arguments, pagination
from handler.base import BaseHandler, HTTPError
from orm.db import session_scope
from orm.models import PublishPattern, PublishPatternHost
from tasks.log_task import audit_log
from worker.pattern import get_publish_hosts
from worker.run_task import run_chain_tasks


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

        ready_host_tasks = {}
        upgrade_plan_finish = False

        with session_scope() as ss:
            try:
                # check pattern status
                pattern = ss.query(PublishPattern).filter_by(id=pattern_id).with_for_update().one()
                if pattern.status == 1:
                    raise HTTPError(status_code=400, reason="请求步骤正在执行中")
            except NoResultFound:
                raise HTTPError(status_code=400, reason="Find pattern id not found: %s" % pattern_id)

            # 检查是否需要最后更新plan状态
            max_step = ss.query(func.max(
                PublishPattern.step)).filter_by(publish_plan_id=pattern.publish_plan_id).one()[0]
            if max_step == pattern.step:
                upgrade_plan_finish = True

            pattern_hosts = ss.query(PublishPatternHost).filter(
                PublishPatternHost.publish_pattern_id == pattern_id).all()

            if not pattern_hosts:
                raise HTTPError(status_code=400, reason="No host on the pattern_id: %s" % pattern_id)
            pattern_hosts = [t.to_dict() for t in pattern_hosts]

            for pattern_host in pattern_hosts:
                tasks = []
                publish_host = pattern_host['publish_host']

                for task in pattern_host['publish_pattern_tasks']:
                    task_name = task['task_name']
                    task_kwargs = {
                        "publish_host_id_list": [publish_host['id']],
                        "task_name": task_name,
                        "pattern_id": pattern_id,
                    }

                    # 主机有执行中的任务就跳出，主机的任务不再重复执行
                    if task['status'] == 1:
                        break

                    # 只执行状态是 0：待执行 3：失败 的任务
                    if task['status'] not in (0, 3):
                        continue

                    tasks.append(task_kwargs)
                if tasks:
                    host_tasks = ready_host_tasks.setdefault(publish_host['host_name'], [])
                    host_tasks.extend(tasks)

            # 链式执行任务
            run_chain_tasks(
                session=ss,
                ready_host_tasks=ready_host_tasks.values(),
                upgrade_plan_finish=upgrade_plan_finish,
                plan_id=pattern.publish_plan_id)

        audit_log(handler=self, description="执行发版步骤", resource_type=4, resource_id=pattern_id)
        self.render_json_response(code=200, res=ready_host_tasks)
