from tornado.web import HTTPError
from handler.base import BaseHandler

from tasks.cmdb_agent import start, refresh, restart, status, stop


class CMDBAgentOperationHandler(BaseHandler):
    def get(self, *args, **kwargs):
        """
        cmd : status/start/stop/refresh
        :param args:
        :param kwargs:
        :return:
        """
        argus = self.url_arguments
        cmdstr = argus.pop('cmd', 'status')
        hosts = argus.pop('hosts', '')
        if not hosts:
            raise HTTPError(status=400, reason="Missing arguments host")
        hosts = hosts.split(',')

        if cmdstr == "status":
            res = status.delay(hosts)
            # res = status.apply_async(args=[hosts])
        elif cmdstr == 'start':
            res = start.delay(hosts)
        elif cmdstr == 'stop':
            res = stop.delay(hosts)
        elif cmdstr == 'restart':
            res = restart.delay(hosts)
        elif cmdstr == 'refresh':
            res = refresh.delay(hosts)
        else:
            raise HTTPError(status_code=400, reason="cmdb must be in [status, start,restart,stop,refresh]")

        result = {'taskid': res.id, 'result': res.result}

        self.render_json_response(code=200, msg="OK", res=result)


