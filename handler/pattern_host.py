from handler.base import BaseWebSocket, BaseHandler, HTTPError
import json
from json.decoder import JSONDecodeError
from orm.models import PublishPatternTask, PublishTask, PublishPatternHost
from orm.db import session_scope
from common.util import take_out_unrightful_arguments
from common.authentication import validate_requests, validate_user_permission
from worker.pattern import upgrade_pattern_status


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
        "res": {
            'publish_task': [],
            'publish_pattern_task': []
        },
    }
    """

    def open(self, callback_timeout=500):
        super().open(callback_timeout=callback_timeout)
        self.limit = 10
        self.offset = 0
        self.pattern_task_status = []

    def on_message(self, message):
        super().on_message(message)
        try:
            message = json.loads(message)
            self.message = message
            self.callback()
        except JSONDecodeError:
            self.render_json_response(code=400, msg='Request arguments format error', res=message)
        except Exception:
            self.render_json_response(code=400, msg='Unknown error on message', res=message)

    def callback(self):
        if self.message is None:
            return

        result = {
            'publish_task': [],
            'publish_pattern_task': []
        }
        publish_tasks = []
        publish_pattern_host_id = self.message['publish_pattern_host_id']

        with session_scope() as ss:
            q = ss.query(PublishTask).join(
                PublishPatternTask, PublishPatternTask.id == PublishTask.publish_pattern_task_id).filter(
                    PublishPatternTask.publish_pattern_host_id == publish_pattern_host_id)
            db_res = q.limit(self.limit).offset(self.offset).all()

            pattern_tasks = ss.query(PublishPatternTask).filter_by(
                publish_pattern_host_id=publish_pattern_host_id).all()

            publish_pattern_task = [t.to_dict() for t in pattern_tasks]
            new_task_status = [t['status'] for t in publish_pattern_task]

            if db_res:
                for t in db_res:
                    if t.status in ('SUCCESS', 'FAILED'):
                        publish_tasks.append(t.to_dict())

                result['publish_task'] = publish_tasks
                self.offset += len(publish_tasks)

            if publish_tasks or new_task_status != self.pattern_task_status:
                self.pattern_task_status = new_task_status
                result['publish_pattern_task'] = publish_pattern_task
                self.render_json_response(res=result)


class PatternHostHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('put')
    def put(self):
        res = {}
        rightful_keys = (
            'id',
            'publish_pattern_id',
            'publish_host_id',
            'status',
        )
        body_kwargs = take_out_unrightful_arguments(rightful_keys, self.body_arguments)

        _id = body_kwargs.pop('id', None)
        pattern_id = body_kwargs.pop('publish_pattern_id', None)
        host_id = body_kwargs.pop('publish_host_id', None)
        if (_id is None) and (pattern_id is None or host_id is None):
            raise HTTPError(status_code=400, reason='"id" or ("publish_pattern_id" and "publish_host_id") is required')

        with session_scope() as ss:
            if _id is not None:
                q = ss.query(PublishPatternHost).filter_by(id=_id).with_for_update()
            else:
                q = ss.query(PublishPatternHost).filter_by(publish_pattern_id=pattern_id, publish_host_id=host_id)

            pattern_host = q.one_or_none()
            if pattern_host is None:
                raise HTTPError(status_code=400, reason='Id not found: %d' % _id)

            q.update(body_kwargs)
            ss.flush()

            new_status = body_kwargs.pop('status', None)
            if new_status is not None:
                for t in pattern_host.publish_pattern_tasks:
                    t.status = new_status
                ss.flush()
                upgrade_pattern_status(ss, pattern_host.publish_pattern_id)

            res = pattern_host.to_dict()

        self.render_json_response(code=200, res=res)
