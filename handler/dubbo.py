from tornado.web import HTTPError

from handler.base import BaseHandler
from orm.db import session_scope
from tasks import dubbo
from worker.run_task import run_celery_task
from worker.commons import audit_log
from common.authentication import validate_requests, validate_user_permission

task_name_map = {
    'status': "查询dubbo状态",
    'enable': "启动dubbo",
    'disable': '停止dubbo',

}


class DubboOperationHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('get')
    def get(self, *args, **kwargs):
        """
        cmd： status/enable/disable
        """
        argus = self.url_arguments
        pattern_id = argus.pop('pattern_id', None)
        cmdstr = argus.pop('cmd', 'status')
        publish_host_ids = argus.pop('publish_host_ids', '')

        if not publish_host_ids or not cmdstr:
            raise HTTPError(status=400, reason="Missing arguments publish_host_ids or cmdstr")
        publish_host_id_list = publish_host_ids.split(',')
        task_name = task_name_map[cmdstr]
        with session_scope() as ss:
            host_and_id_list = run_celery_task(
                session=ss,
                publish_host_id_list=publish_host_id_list,
                task_name=task_name,
                pattern_id=pattern_id)

        for resource_id in publish_host_id_list:
            audit_log(self, description=task_name, resource_type=3, resource_id=resource_id)
        self.render_json_response(code=200, msg="OK", res=host_and_id_list)
