from handler.base import BaseWebSocket
import json
from json.decoder import JSONDecodeError
from orm.models import PublishPatternTask, AnsibleTaskResult, PublishTask
from orm.db import session_scope


class PatternHostTaskWebSocket(BaseWebSocket):
    """
    request arguments:
    {
        "publish_pattern_host_id": 0
    }

    response:
    {
        "code": 200,
        "msg": "",
        "res": "",
    }
    """

    def open(self, callback_timeout=500):
        super(PatternHostTaskWebSocket, self).open(callback_timeout=callback_timeout)
        self.limit = 10
        self.offset = 0
        self.pattern_task_status = []

    def on_message(self, message):
        try:
            message = json.loads(message)
            self.message = message
        except JSONDecodeError:
            self.render_json_response(code=400, msg='Request arguments format error', res=message)
        except Exception:
            self.render_json_response(code=400, msg='Unknown error on message', res=message)

    def callback(self):
        if self.message is None:
            return

        result = {
            'ansible_task_result': [],
            'publish_pattern_task': []
        }
        ansible_tasks = []
        publish_pattern_host_id = self.message['publish_pattern_host_id']

        with session_scope() as ss:
            q = ss.query(AnsibleTaskResult, PublishTask.task_name).join(
                PublishTask, PublishTask.celery_task_id == AnsibleTaskResult.celery_task_id).join(
                    PublishPatternTask, PublishPatternTask.id == PublishTask.publish_pattern_task_id).filter(
                        PublishPatternTask.publish_pattern_host_id == publish_pattern_host_id)
            db_res = q.limit(self.limit).offset(self.offset).all()

            pattern_tasks = ss.query(PublishPatternTask).filter_by(
                publish_pattern_host_id=publish_pattern_host_id).all()

            publish_pattern_task = [t.to_dict() for t in pattern_tasks]
            new_task_status = [t['status'] for t in publish_pattern_task]

            if db_res:
                for ansible_result, task_name in db_res:
                    d = ansible_result.to_dict()
                    d['task_name'] = task_name
                    ansible_tasks.append(d)

                result['ansible_task_result'] = ansible_tasks
                self.offset += len(db_res)

            if db_res or new_task_status != self.pattern_task_status:
                self.pattern_task_status = new_task_status
                result['publish_pattern_task'] = publish_pattern_task
                self.render_json_response(res=result)
