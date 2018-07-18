from celery_worker import app
from conf import settings
from tasks.base import AnsibleTask
from worker.commons import run_ansible

SHELL_SCRIPT = settings['sh_path'] + '/service.sh'


def run_shell(host, cmd, project_name):
    if project_name:
        cmdstr = SHELL_SCRIPT + ' ' + project_name + ' ' + cmd
    else:
        cmdstr = SHELL_SCRIPT + ' ' + cmd
    res = run_ansible(cmdstr, host, become=False, become_user=None)
    return res


@app.task(base=AnsibleTask)
def start(host, project_name=None):
    cmd = 'start'
    return run_shell(host, cmd, project_name)


@app.task(base=AnsibleTask)
def stop(host, project_name=None):
    cmd = 'stop'
    return run_shell(host, cmd, project_name)


@app.task(base=AnsibleTask)
def restart(host, project_name=None):
    cmd = 'restart'
    return run_shell(host, cmd, project_name)


@app.task(base=AnsibleTask)
def status(host, project_name=None):
    cmd = 'status'
    return run_shell(host, cmd, project_name)


@app.task(base=AnsibleTask)
def list(host, project_name=None):
    cmd = 'list'
    return run_shell(host, cmd, project_name)
