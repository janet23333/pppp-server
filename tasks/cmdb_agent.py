from celery_worker import app
# from celery.utils.log import get_task_logger
from worker.commons import run_ansible
from conf import settings

from tasks.base import CallbackTask

SHELL_SCRIPT = 'sh -x ' + settings['sh_path'] + '/cmdb-agent.sh'


# logger = get_task_logger(__name__)


@app.task(base=CallbackTask)
def start(host):
    cmdstr = SHELL_SCRIPT + ' ' + 'start'
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    return res


@app.task(base=CallbackTask)
def status(host):
    # logger.info('status {} '.format(hosts))
    cmdstr = SHELL_SCRIPT + ' ' + 'status'
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    return res


@app.task(base=CallbackTask)
def refresh(host):
    cmdstr = SHELL_SCRIPT + ' ' + 'refresh'
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    return res


@app.task
def restart(host):
    cmdstr = SHELL_SCRIPT + ' ' + 'restart'
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    return res


@app.task
def stop(host):
    cmdstr = SHELL_SCRIPT + ' ' + 'stop'
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    return res
