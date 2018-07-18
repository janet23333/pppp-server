from celery.utils.log import get_task_logger

from celery_worker import app
from conf import settings
from tasks.base import AnsibleTask
from worker.commons import run_ansible

logger = get_task_logger(__name__)


@app.task(base=AnsibleTask)
def run(host, script, become_user=None, *arguments, **kwargs):
    logger.warning(
        'host: {host}, script: {script}, become_user: {become_user}, arguments: {arguments}, kwargs: {kwargs}'.format(
            host=host, script=script, become_user=become_user, arguments=arguments, kwargs=kwargs))

    cmdstr = '{sh_path}/{script}'.format(sh_path=settings['sh_path'], script=script)
    for arg in arguments:
        cmdstr += ' %s' % arg

    become = True
    if become_user is None or become_user == '':
        become = False

    res = run_ansible(cmdstr, host, become=become, become_user=become_user)
    return res
