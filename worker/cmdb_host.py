from conf import settings

url = settings['cmdb_server']['url']
token = settings['cmdb_server']['token']
api = '{}/host/?application_name='.format(url)
token = {'token': token}


def set_master_slave_host(res):
    gray_host = list(filter(lambda x: x['flag'] == 2, res))
    not_gray_host = list(filter(lambda x: x['flag'] != 2, res))

    for i, item in enumerate(not_gray_host):
        if i % 2 == 0:
            item['host_deploy_type'] = 'master'
        else:
            item['host_deploy_type'] = 'slave'

    def assign_gray(x):
        x['host_deploy_type'] = "gray"
        return x

    gray_host = list(map(assign_gray, gray_host))
    not_gray_host.extend(gray_host)
    return not_gray_host
