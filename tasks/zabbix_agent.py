from celery_worker import app
from worker.commons import run_ansible
from conf import settings

SHELL_SCRIPT = 'sh -x ' + settings['remote_sh_path'] + '/zabbix_agent.sh'


@app.task
def start(host):
    cmdstr = SHELL_SCRIPT + ' ' + 'start'
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    return res


@app.task
def status(host):
    cmdstr = SHELL_SCRIPT + ' ' + 'status'
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
