from celery_worker import app
from worker.commons import run_ansible
from conf import settings
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

shell_script = 'sh -x {}/rollback.sh'.format(settings['remote_sh_path'])


@app.task
def run(host, version, project_name):
    cmdstr = '{} {} {}'.format(shell_script, project_name, version)
    logger.info(cmdstr)
    res = run_ansible(cmdstr, host, become=False, become_user=None, module='shell')
    logger.info(res)
    return res
