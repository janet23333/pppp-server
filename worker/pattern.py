from orm.models import PublishPattern, PublishPatternHost
from worker.commons import check_status
from tornado.log import app_log


def get_publish_hosts(publish_pattern):
    application_id_map = dict()

    for pattern_host in publish_pattern.publish_pattern_host_list:
        publish_host = pattern_host.publish_host
        publish_application_id = publish_host.publish_application_id

        # 主机按应用分类
        if publish_application_id not in application_id_map:
            publish_application = publish_host.publish_application.to_dict()
            app_map = application_id_map.setdefault(publish_application_id, {})
            app_map['publish_application'] = publish_application

        # 获取主机tasks
        publish_host_dict = publish_host.to_dict()
        publish_host_dict['status'] = pattern_host.status
        publish_host_dict['tasks'] = []
        for task in pattern_host.publish_pattern_tasks:
            if task.publish_pattern_host.publish_host_id == publish_host.id:
                publish_host_dict['tasks'].append(task.to_dict())

        host_list = application_id_map[publish_application_id].setdefault('publish_hosts', [])
        host_list.append(publish_host_dict)

    return list(application_id_map.values())


def upgrade_pattern_status(ss, publish_pattern_id):
    q = ss.query(PublishPatternHost.status).filter_by(publish_pattern_id=publish_pattern_id).all()
    hosts_status = [i[0] for i in q]
    status = check_status(hosts_status)
    app_log.debug('upgrade pattern status, status is %s' % status)

    pattern = ss.query(PublishPattern).filter_by(id=publish_pattern_id).with_for_update().one()
    pattern.status = status

    ss.flush()
    return pattern
