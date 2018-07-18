from tornado.web import HTTPError

from common.authentication import validate_requests, validate_user_permission
from handler.base import BaseHandler
from orm.db import session_scope
from orm.models import PublishPattern, PublishPlan
from tasks.log_task import audit_log
from worker.pattern import get_publish_hosts
from worker.rollback import get_host_by_publish_plan_id, generate_rollback_steps, run_rollback_pattern
from worker.rollback import get_retry_rollback_pattern_ids
from worker.run_task import run_celery_task, run_chain_tasks, get_action_tasks


class RollbackOperationHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('post')
    def post(self):
        argus = self.body_arguments
        publish_plan_id = argus.pop('publish_plan_id', None)
        if not publish_plan_id:
            raise HTTPError(status_code=400, reason='Missing arguments: publish_plan_id')
        res = []

        host_application_list = get_host_by_publish_plan_id(publish_plan_id)
        if not host_application_list:
            raise HTTPError(
                status_code=400, reason="publish_plan_id {} has no finished pattern".format(publish_plan_id))
        all_pattern_id_list = generate_rollback_steps(publish_plan_id, host_application_list)

        with session_scope() as ss:
            #  update publish plan status
            ss.query(PublishPlan).filter_by(id=publish_plan_id).update({"status": 21})

            # 把QA测试的步骤去掉
            p_res = ss.query(PublishPattern).filter(PublishPattern.action > 10, PublishPattern.action != 13,
                                                    PublishPattern.id.in_(all_pattern_id_list)).order_by(
                PublishPattern.step).all()
            pattern_id_list = []
            for pattern in p_res:
                # 有停顿， 不再往下
                if pattern.action == 19:
                    break
                pattern_id_list.append(pattern.id)

            for pattern_id in pattern_id_list:
                audit_log(handler=self, description="执行回滚步骤", resource_type=4, resource_id=pattern_id)

        ready_run_tasks = run_rollback_pattern(pattern_id_list)

        with session_scope() as ss:
            db_res = ss.query(PublishPattern).filter(PublishPattern.id.in_(pattern_id_list)).all()
            for pattern in db_res:
                r = pattern.to_dict()
                r['publish_application_hosts'] = get_publish_hosts(pattern)
                res.append(r)
        res.append({'ready_run_task': ready_run_tasks})

        self.render_json_response(code=200, msg="OK", res=res)


class RollbackRetryHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('post')
    def post(self):
        argus = self.body_arguments
        publish_plan_id = argus.pop('publish_plan_id', None)
        if not publish_plan_id:
            raise HTTPError(status_code=400, reason='Missing arguments: publish_plan_id')
        res = []
        with session_scope() as ss:
            publish_plan = ss.query(PublishPlan).filter_by(id=publish_plan_id).one_or_none()
            if not publish_plan or publish_plan.status != 21:
                raise HTTPError(status_code=400,
                                reason=' publish_plan_id {} is not exits or not in rollback status'.format(
                                    publish_plan_id))
        retry_pattern_id_list = get_retry_rollback_pattern_ids(publish_plan_id)
        if not retry_pattern_id_list:
            raise HTTPError(status_code=400, reason="Has no retry_patterns to retry")
        ready_run_tasks = run_rollback_pattern(retry_pattern_id_list)
        with session_scope() as ss:
            db_res = ss.query(PublishPattern).filter(PublishPattern.id.in_(retry_pattern_id_list)).all()
            for pattern in db_res:
                r = pattern.to_dict()
                r['publish_application_hosts'] = get_publish_hosts(pattern)
                res.append(r)
        res.append({'ready_run_task': ready_run_tasks})

        self.render_json_response(code=200, msg="OK", res=res)


class RollbackHostHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('post')
    def post(self):
        argus = self.body_arguments
        res = []
        with session_scope() as ss:
            for item in argus:
                application_name = item.pop('application_name', None)
                application_type = item.pop('application_type', None)
                publish_host_ids = item.pop('publish_host_ids', None)
                if not publish_host_ids or not application_name or not application_type:
                    raise HTTPError(status_code=400, reason="Missing argument ,please check")

                ready_host_tasks = []
                for publish_host_id in publish_host_ids:
                    tasks = get_action_tasks(
                        action=11, application_type=application_type, application_name=application_name)
                    tasks = [{'publish_host_id_list': [publish_host_id], 'task_name': t} for t in tasks]
                    ready_host_tasks.append(tasks)
                host_and_id_list = run_chain_tasks(session=ss, ready_host_tasks=ready_host_tasks)

                res.extend(host_and_id_list)
                for resource_id in publish_host_ids:
                    audit_log(self, description='执行回滚', resource_type=3, resource_id=resource_id)
        self.render_json_response(code=200, msg="OK", res=res)
