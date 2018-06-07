from common.util import run_shell


def get_publish_host(file):
    cmd = "cat {} | egrep -v '^\[|^$'|sort -u |sed 's/#//g'".format(file)
    result = run_shell(cmd)
    if result.startswith('error'):
        return result
    publish_host_list = {}
    application_type = {}
    for line in result.split('\n'):
        data = line.split()
        host_ip = data[0]
        host_name = data[1]
        app_type = data[2]
        application_name_id = data[3]
        application_version = data[-1] if data[-1].split('-')[-1].isdigit() else '0'
        if application_name_id not in application_type:
            application_type.update({application_name_id: app_type})
        host_dict = {'host_ip': host_ip, 'host_name': host_name, 'rollback_version': application_version, 'progress': 1}
        if application_name_id in publish_host_list:
            publish_host_list[application_name_id].append(host_dict)
        else:
            publish_host_list.update({application_name_id: [host_dict]})
    return publish_host_list, application_type
