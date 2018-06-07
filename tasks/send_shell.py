import os

from celery_worker import app
from worker.commons import run_ansible
from conf import settings


# 暂时不可用 copy 模块有些问题
#
@app.task
def run(host):
    """
    :param hosts:  can be ip or host group name
    :return:
    """
    BASE_DIR = os.getcwd()

    src = BASE_DIR + '/sh/'
    dest = settings['remote_sh_path'] + "/"

    cmdstr = "src={} dest={}".format(src, dest)
    # res = run_ansible(cmdstr, hosts, become=False, become_user=None, module="synchronize")
    # nginx_sh = src + "nginx.sh"
    res = run_ansible(cmdstr, host, become=False, become_user=None, module="copy")
    # cmd = 'ansible all -m copy -a 'src=/tmp/yan/publish-server/sh/ dest=/data/sh/ force=Yes' -u root'
    return res



