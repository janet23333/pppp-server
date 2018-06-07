from celery_worker import app
from worker.commons import run_ansible
from conf import settings
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)
shell_script = 'sh -x {}/get_package.sh'.format(settings['remote_sh_path'])


@app.task
def get_package(host, version, project_name=None):
    if project_name:
        cmdstr = '{} {} {}'.format(shell_script, project_name, version)
    else:
        cmdstr = '{} {}'.format(shell_script, version)
    logger.info(cmdstr)
    res = run_ansible(cmdstr, host, become=False)
    logger.info(res)
    return res
