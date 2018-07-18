from orm.models import PublishTask
from datetime import datetime


def add_publish_task(session, task_id, task_name, publish_host_id, pattern_task_id=0, status="PENDING"):
    publish_task = PublishTask()
    publish_task.publish_pattern_task_id = pattern_task_id
    publish_task.publish_host_id = publish_host_id
    publish_task.celery_task_id = task_id
    publish_task.status = status
    publish_task.task_name = task_name
    publish_task.start_time = datetime.now()
    session.add(publish_task)

    session.flush()
    return publish_task
