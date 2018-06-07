import celery
from tornado.log import app_log

from celery_worker import app
from orm.db import session_scope
from orm.models import AuditLog, HostLog


class AuditError(Exception):
    pass


class CallbackTask(celery.Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        app_log.error('Write audit log error, taskid: {task_id}, args: {args},  kwargs: {kwargs}, msg: {exc}'.format(
            task_id=str(task_id), args=str(args), kwargs=str(kwargs), exc=str(exc)))


@app.task(base=CallbackTask)
def insert_audit_log(**kwargs):
    with session_scope() as ss:
        auditlog = AuditLog(**kwargs)
        ss.add(auditlog)


@app.task(base=CallbackTask)
def insert_host_log(host, task_name, task_status):
    with session_scope() as ss:
        host_log = HostLog()
        host_log.host_name = host['host_name']
        host_log.host_ip = host['host_ip']
        host_log.publish_host_id = host['publish_host_id']
        host_log.task_name = task_name
        host_log.task_status = task_status
        ss.add(host_log)
