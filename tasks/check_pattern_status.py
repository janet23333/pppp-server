import time

from celery.utils.log import get_task_logger

from celery_worker import app
from orm.db import session_scope
from orm.models import PublishPattern
from tasks.base import CheckTask

logger = get_task_logger(__name__)


@app.task(base=CheckTask)
def check_pattern_status(pattern_id, **kwargs):
    start = time.time()
    while True and (time.time() - start) < 15 * 60:
        with session_scope() as ss:
            status = ss.query(PublishPattern.status).filter_by(id=pattern_id).one()[0]
            if status == 2:  # 成功
                return True
            elif status == 3:  # 失敗
                return False
            time.sleep(0.4)
    return False
