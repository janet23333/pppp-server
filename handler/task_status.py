from tornado.web import HTTPError

from handler.base import BaseHandler, BaseWebSocket
from orm.db import session_scope
from orm.models import PublishTask


class TaskStatusHandler(BaseHandler):
    def get(self):
        argus = self.url_arguments
        taskids = argus.pop('taskids', None)
        taskids = taskids.split(',')
        if not taskids:
            raise HTTPError(status_code=400, reason='Missing  arguments taskids')
        with session_scope() as ss:
            q = ss.query(PublishTask).filter(PublishTask.celery_task_id.in_(taskids)).all()
            res = [task.to_dict() for task in q]

        self.render_json_response(code=200, msg='OK', res=res)


class TaskStatusWebSocket(BaseWebSocket):
    def open(self, callback_timeout=500):
        super().open(callback_timeout=callback_timeout)
        self.taskids = []

    def on_message(self, message):
        super().on_message(message)
        self.taskids.append(message)

    def callback(self):
        if len(self.taskids) > 0:
            try:
                _temp_ids = []
                with session_scope() as ss:
                    for task_id in self.taskids:
                        qq = ss.query(PublishTask).filter(PublishTask.celery_task_id == task_id).first()
                        res = qq.to_dict() if qq else {}
                        if res.get('status') == 'SUCCESS':
                            self.render_json_response(res)
                            _temp_ids.append(task_id)
                self.taskids = [x for x in self.taskids if x not in _temp_ids]
            except Exception as inst:
                self.render_json_response("Inter Server Error ： {}".format(inst))
