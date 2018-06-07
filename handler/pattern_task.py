from handler.base import BaseWebSocket
import json
from json.decoder import JSONDecodeError
from orm.models import PublishPatternTask, PublishPatternHost, PublishPattern
from orm.db import session_scope
from worker.pattern import get_publish_hosts


class PatternTaskWebSocket(BaseWebSocket):
    """
    获取pattern task信息
    request arguments:
    {
        "pattern_id": 0
    }

    response:
    {
        "code": 200,
        "msg": "",
        "res": "",
    }
    """

    def open(self, callback_timeout=500):
        super(PatternTaskWebSocket, self).open(callback_timeout=callback_timeout)
        self.tasks_status = {}
        self.patterns_status = {}

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

        with session_scope() as ss:
            pattern_id = self.message['pattern_id']

            # 对比pattern状态
            new_pattern_status = ss.query(PublishPattern.status).filter_by(id=pattern_id).one_or_none()
            if new_pattern_status is None:
                self.render_json_response(code=400, msg='Pattern id %s not found' % pattern_id, res=self.message)
            new_pattern_status = new_pattern_status[0]

            pattern_status = self.patterns_status.get(pattern_id, 0)
            if new_pattern_status != pattern_status:
                self.patterns_status[pattern_id] = new_pattern_status
                self.render_pattern(ss, pattern_id)
                return

            # 对比pattern下所有task状态
            db_res = ss.query(PublishPatternTask.status).join(
                PublishPatternHost, PublishPatternHost.id == PublishPatternTask.publish_pattern_host_id).join(
                    PublishPattern, PublishPattern.id == PublishPatternHost.publish_pattern_id).filter(
                        PublishPattern.id == pattern_id).all()
            new_tasks_status = [d[0] for d in db_res]

            old_tasks_status = self.tasks_status.get(pattern_id, [])
            if old_tasks_status != new_tasks_status:
                self.tasks_status[pattern_id] = new_tasks_status
                self.render_pattern(ss, pattern_id)
                return

    def render_pattern(self, ss, pattern_id):
        pattern = ss.query(PublishPattern).filter_by(id=pattern_id).one()
        result = pattern.to_dict()
        result['publish_application_hosts'] = get_publish_hosts(pattern)

        self.render_json_response(res=result)
