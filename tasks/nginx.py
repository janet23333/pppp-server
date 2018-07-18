from celery.utils.log import get_task_logger

from celery_worker import app
from conf import settings
from tasks.base import AnsibleTask
from worker.commons import run_ansible

logger = get_task_logger(__name__)

SHELL_SCRIPT = settings['sh_path'] + '/nginx.sh'


@app.task(base=AnsibleTask)
def start(host):
    cmdstr = '{} start'.format(SHELL_SCRIPT)
    logger.info(cmdstr)
    res = run_ansible(cmdstr, host, become=True, become_user='root')
    logger.info(res)
    return res


@app.task(base=AnsibleTask)
def status(host):
    cmdstr = '{} status'.format(SHELL_SCRIPT)
    res = run_ansible(cmdstr, host, become=True, become_user='root')
    return res


@app.task(base=AnsibleTask)
def reload(host):
    cmdstr = '{} reload'.format(SHELL_SCRIPT)
    res = run_ansible(cmdstr, host, become=True, become_user="root")
    return res


@app.task(base=AnsibleTask)
def restart(host):
    cmdstr = '{} restart'.format(SHELL_SCRIPT)
    res = run_ansible(cmdstr, host, become=True, become_user="root")
    return res


@app.task(base=AnsibleTask)
def stop(host):
    cmdstr = '{} stop'.format(SHELL_SCRIPT)
    logger.info(cmdstr)
    res = run_ansible(cmdstr, host, become=True, become_user='root')
    logger.info(res)
    return res


@app.task(base=AnsibleTask)
def configtest(host):
    cmdstr = '{} configtest'.format(SHELL_SCRIPT)
    res = run_ansible(cmdstr, host, become=True, become_user="root")
    return res
