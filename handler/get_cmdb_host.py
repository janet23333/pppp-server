import copy

from common.authentication import validate_requests, validate_user_permission
from handler.base import BaseHandler
from worker.commons import get_cmdb_host
from worker.inventory_for_cmdb import set_master_slave_host


class CMDBHostHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('get')
    def get(self, *args, **kwargs):
        argus = self.url_arguments
        application_name_list = argus.get('application_name').split(',')
        # kwargs.update({'sort_prop': "hostname"})
        res = get_cmdb_host(argus)

        app_host_dict = dict()
        total_host_dict = dict()
        for item in res:
            app_list = item['application_list']
            app_name_list = list(map(lambda x: x['application']['name'], app_list))
            for app_name in app_name_list:
                if app_name in application_name_list:
                    if app_name in app_host_dict.keys():
                        app_host_dict[app_name].append(copy.deepcopy(item))
                    else:
                        app_host_dict[app_name] = [copy.deepcopy(item)]

        for app_name, hosts in app_host_dict.items():
            hosts.sort(key=lambda x: x['hostname'])
            hosts = set_master_slave_host(hosts)
            total_host_dict.setdefault(app_name, hosts)

        self.render_json_response(code=200, msg="OK", res=total_host_dict)
