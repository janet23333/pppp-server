from celery_worker import app
from worker.commons import run_ansible
from conf import settings

# SHELL_SCRIPT = settings['sh_path'] + '/sh/service.sh'
SHELL_SCRIPT = 'sh -x ' + settings['remote_sh_path'] + '/service.sh'


def run_shell(host, cmd, project_name):
    if project_name:
        cmdstr = SHELL_SCRIPT + ' ' + project_name + ' ' + cmd
    else:
        cmdstr = SHELL_SCRIPT + ' ' + cmd
    res = run_ansible(cmdstr, host, become=False, become_user=None, module='shell')
    return res


@app.task
def start(host, project_name=None):
    cmd = 'start'
    return run_shell(host, cmd, project_name)


@app.task
def stop(host, project_name=None):
    cmd = 'stop'
    return run_shell(host, cmd, project_name)


@app.task
def restart(host, project_name=None):
    cmd = 'restart'
    return run_shell(host, cmd, project_name)


@app.task
def status(host, project_name=None):
    cmd = 'status'
    return run_shell(host, cmd, project_name)


@app.task
def list(host, project_name=None):
    cmd = 'list'
    return run_shell(host, cmd, project_name)
