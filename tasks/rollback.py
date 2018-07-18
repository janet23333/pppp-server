from celery.utils.log import get_task_logger

from celery_worker import app
from conf import settings
from tasks.base import AnsibleTask
from worker.commons import run_ansible

logger = get_task_logger(__name__)

SHELL_SCRIPT = settings['sh_path'] + '/rollback.sh'


@app.task(base=AnsibleTask)
def run(host, version, project_name, **kwargs):
    cmdstr = '{} {} {}'.format(SHELL_SCRIPT, project_name, version)
    logger.info(cmdstr)
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    logger.info(res)
    return res
