from celery_worker import app
from worker.commons import run_ansible
from conf import settings
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

shell_script = 'sh -x {}/dubbo.sh'.format(settings['remote_sh_path'])


@app.task
def status(host):
    cmdstr = shell_script + ' ' + 'status'
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    return res


@app.task
def enable(host):
    cmdstr = '{} enable'.format(shell_script)
    logger.info(cmdstr)
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    logger.info(res)
    return res

@app.task
def disable(host):
    cmdstr = '{} disable'.format(shell_script)
    logger.info(cmdstr)
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    logger.info(res)
    return res
