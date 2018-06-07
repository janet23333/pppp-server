from tornado.web import HTTPError

from conf import settings
from handler.base import BaseHandler
from worker.commons import run_ansible

shell_script = '{}/get_package.sh'.format(settings['sh_path'])


class OperationHandler(BaseHandler):
    def get(self, *args, **kwargs):
        argus = self.url_arguments
        project_name = argus.pop('project_name', '')
        hosts = argus.pop('hosts', '')
        version = argus.pop('version', '')

        if not hosts or not project_name or not version:
            raise HTTPError(status_code=400, reason="Missing argument hosts/version/project_name")
        hosts = hosts.split(',')
        res = []
        for host in hosts:
            cmdstr = '{} {} {}'.format(shell_script, project_name, version)

            result = run_ansible(cmdstr, host, become=False, module='script')
            res.append(result)
        self.render_json_response(code=200, msg="OK", res=res)
