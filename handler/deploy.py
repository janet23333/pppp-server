from tornado.web import HTTPError

from common.authentication import validate_requests, validate_user_permission
from handler.base import BaseHandler
from orm.db import session_scope
from tasks.log_task import audit_log
from worker.run_task import run_celery_task


class DeployOperationHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('post')
    def post(self, *args, **kwargs):
        argus = self.body_arguments
        if not isinstance(argus, list):
            raise HTTPError(status_code=400, reason='arguments must be list')
        res = []
        with session_scope() as ss:
            for item in argus:
                pattern_id = item.pop('pattern_id', None)
                version = item['version']
                project_name = item.pop('application_name', None)
                publish_host_ids = item.pop('publish_host_ids', None)
                if not (project_name or version or publish_host_ids or pattern_id):
                    raise HTTPError(status_code=400, reason="Missing arguments")

                task_name = '执行发版'
                host_and_id_list = run_celery_task(
                    session=ss,
                    publish_host_id_list=publish_host_ids,
                    task_name=task_name,
                    pattern_id=pattern_id,
                    version=version,
                    project_name=project_name)
                res.extend(host_and_id_list)
                for resource_id in publish_host_ids:
                    audit_log(self, description=task_name, resource_type=3, resource_id=resource_id)
        self.render_json_response(code=200, msg="OK", res=res)
