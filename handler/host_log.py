import json
from json import JSONDecodeError

from handler.base import BaseWebSocket
from orm.db import session_scope
from orm.models import HostLog


class HostLogWebSocket(BaseWebSocket):
    def open(self, callback_timeout=500):
        super(HostLogWebSocket, self).open(callback_timeout=callback_timeout)
        self.total = 0

    def on_message(self, message):
        try:
            message = json.loads(message)
            self.message = message
        except JSONDecodeError:
            self.render_json_response(code=400, msg='Request arguments format error', res=message)
        except Exception:
            self.render_json_response(code=400, msg='Unknown error on message', res=message)

    def callback(self):
        publish_host_id = self.message['publish_host_id']
        with session_scope() as session:
            q = session.query(HostLog).filter(HostLog.publish_host_id == publish_host_id)

            total = q.count()
            if total != self.total:
                res = q.offset(self.total).all()
                res = [r.to_dict() for r in res]

                self.total = total
                self.render_json_response(res=res)
