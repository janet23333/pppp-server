from celery.utils.log import get_task_logger

from celery_worker import app
from conf import settings
from tasks.base import AnsibleTask
from worker.commons import run_ansible

logger = get_task_logger(__name__)
SHELL_SCRIPT = settings['sh_path'] + '/get_package.sh'


@app.task(base=AnsibleTask)
def get_package(host, version, project_name, **kwargs):
    if project_name:
        cmdstr = '{} {} {}'.format(SHELL_SCRIPT, project_name, version)
    else:
        cmdstr = '{} {}'.format(SHELL_SCRIPT, version)
    logger.info(cmdstr)
    res = run_ansible(cmdstr, host, become=False)
    logger.info(res)
    return res
