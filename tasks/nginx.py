from celery_worker import app
from worker.commons import run_ansible
from conf import settings
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

shell_script = 'sh -x {}/nginx.sh'.format(settings['remote_sh_path'])


@app.task
def start(host):
    cmdstr = '{} start'.format(shell_script)
    logger.info(cmdstr)
    res = run_ansible(cmdstr, host, become=True, become_user='root')
    logger.info(res)
    return res


@app.task
def status(host):
    cmdstr = '{} status'.format(shell_script)
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    return res


@app.task
def reload(host):
    cmdstr = '{} reload'.format(shell_script)
    res = run_ansible(cmdstr, host, become=True, become_user="root")
    return res


@app.task
def restart(host):
    cmdstr = '{} restart'.format(shell_script)
    res = run_ansible(cmdstr, host, become=True, become_user="root")
    return res


@app.task
def stop(host):
    cmdstr = '{} stop'.format(shell_script)
    logger.info(cmdstr)
    res = run_ansible(cmdstr, host, become=True, become_user='root')
    logger.info(res)
    return res


@app.task
def configtest(host):
    cmdstr = '{} configtest'.format(shell_script)
    res = run_ansible(cmdstr, host, become=True, become_user="root")
    return res
