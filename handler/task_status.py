from celery.result import AsyncResult
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

    def get_task_resutl(self, ss, taskid):
        qq = ss.query(PublishTask).filter(PublishTask.celery_task_id == taskid).first()
        res = qq.to_dict() if qq else {}
        return res

    def on_message(self, taskids):
        taskids = taskids.split(',')
        pending_task = []
        with session_scope() as ss:
            for taskid in taskids:
                async_result = AsyncResult(taskid)
                ready_index = async_result.ready()
                if ready_index:
                    res = self.get_task_resutl(ss, taskid)
                    self.render_json_response(res)
                else:
                    res = self.get_task_resutl(ss, taskid)
                    self.render_json_response(res)
                    pending_task.append(async_result)
        self.pending_task = pending_task

    def callback(self):
        # pass
        if self.pending_task and len(self.pending_task) > 0:
            try:
                with session_scope() as ss:
                    for task in self.pending_task:
                        # if task.status in ['FAILURE', 'SUCCESS']:
                        ready_index = task.ready()
                        if ready_index:
                            task_id = task.id
                            res = self.get_task_resutl(ss, task_id)
                            self.render_json_response(res)
                            self.pending_task.remove(task)
                        else:
                            task_id = task.id
                            res = self.get_task_resutl(ss, task_id)
                            self.render_json_response(res)

            except Exception as inst:
                self.render_json_response("Inter Server Error ： {}".format(inst))
