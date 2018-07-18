import datetime
import json
from json import JSONDecodeError

from handler.base import BaseWebSocket
from orm.db import session_scope
from orm.models import PublishTask


class HostLogWebSocket(BaseWebSocket):
    def open(self, callback_timeout=500):
        super().open(callback_timeout=callback_timeout)
        self.limit = 10
        self.offset = 0
        self.last_time = datetime.datetime.now()

    def on_message(self, message):
        super().on_message(message)
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

        publish_host_id = self.message['publish_host_id']

        with session_scope() as ss:
            q = ss.query(PublishTask).filter(PublishTask.publish_host_id == publish_host_id)
            db_res = q.limit(self.limit).offset(self.offset).all()

            if db_res:

                res = [r.to_dict() for r in db_res]
                self.offset += len(db_res)

                self.render_json_response(res=res)
            else:
                update_res = ss.query(PublishTask).filter(PublishTask.publish_host_id == publish_host_id,
                                                          PublishTask.update_time > self.last_time).all()
                if update_res:
                    res = [r.to_dict() for r in update_res]
                    self.last_time = datetime.datetime.now()
                    self.render_json_response(res=res)
