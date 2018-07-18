import celery
from celery.utils.log import get_task_logger

from celery_worker import app
from orm.db import session_scope
from orm.models import AuditLog

logger = get_task_logger(__name__)


class LogTask(celery.Task):
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(
            'my task success and taskid is {} ,retval is{} ,args is{}.kwargs id {}'.format(task_id, retval, args,
                                                                                           kwargs))

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))


@app.task(base=LogTask)
def insert_audit_log(**kwargs):
    with session_scope() as ss:
        auditlog = AuditLog(**kwargs)
        ss.add(auditlog)


def audit_log(handler, description, resource_type, resource_id, visible=True):
    if visible:
        visible_ = 1
    else:
        visible_ = 0

    insert_audit_log.delay(
        user_id=handler.user['id'],
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        visible=visible_,
        method=handler.request.method,
        path=handler.request.path,
        fullpath=handler.request.protocol + '://' + handler.request.host + handler.request.uri,
        body=handler.request.body)
