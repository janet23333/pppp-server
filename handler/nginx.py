from tornado.web import HTTPError

from handler.base import BaseHandler
from orm.db import session_scope

from tasks import nginx
from worker.run_task import run_celery_task
from worker.commons import audit_log
from common.authentication import validate_requests, validate_user_permission

task_name_map = {
    'status': "查询nginx状态",
    'start': "启动nginx",
    'stop': '停止nginx',
    'restart': "重启nginx",
    'configtest': '检测conf 文件是否有效',
    'reload': 'nginx reload'
}


class NginxOperationHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('get')
    def get(self, *args, **kwargs):
        '''
        cmd support : status /start/stop/reload/restart/check
        hosts: only support app hosts
        '''
        argus = self.url_arguments
        pattern_id = argus.pop('pattern_id', None)
        cmdstr = argus.pop('cmd', None)
        publish_host_ids = argus.pop('publish_host_ids', None)
        publish_host_id_list = publish_host_ids.split(',')

        if not publish_host_ids or not cmdstr:
            raise HTTPError(status=400, reason="Missing arguments publish_host_ids")
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
