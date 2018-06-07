from  tornado.web import HTTPError
from handler.base import BaseHandler
from tasks import send_shell


class SendShellHandler(BaseHandler):
    def get(self, *args, **kwargs):
        argus = self.url_arguments
        hosts = argus.pop("hosts", None)
        if not hosts:
            raise HTTPError(status_code=400, reason="Missing argument hosts,host can be ip or host group name")
        hosts = hosts.split(',')
        # res = send_shell.run.delay(hosts)
        res = send_shell.run(hosts)
        # result = {'taskid': res.id}

        # self.render_json_response(code=200, msg="OK", res=result)
        self.render_json_response(code=200, msg="OK", res=res)
