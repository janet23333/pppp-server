from orm.models import PublishPatternHost, PublishPatternTask
from worker.commons import check_status


def upgrade_pattern_host_status(ss, publish_pattern_host_id):
    q = ss.query(PublishPatternTask.status).filter_by(publish_pattern_host_id=publish_pattern_host_id).all()
    tasks_status = [i[0] for i in q]
    status = check_status(tasks_status)

    pattern_hosts = ss.query(PublishPatternHost).filter_by(id=publish_pattern_host_id).with_for_update().all()
    for h in pattern_hosts:
        h.status = status

    ss.flush()
    return pattern_hosts
