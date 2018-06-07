from celery.utils.log import get_task_logger

from celery_worker import app
from common.error import ArchivePakageException
from common.error import InvalidUrlException
from orm.db import session_scope
from orm.models import PublishApplication
from worker.archive_package import archive_package
from worker.download_package import package

logger = get_task_logger(__name__)


@app.task
def down_load_and_archive_package(jenkins_url_list, inventory_version, publish_plan_id):
    """ by jenkins url download filename """
    download_package_result = package(jenkins_url_list, inventory_version)
    if download_package_result.startswith('error'):
        logger.error(download_package_result)
        raise InvalidUrlException
    """ archive_package """
    archive_package_list = archive_package(inventory_version)
    if str(archive_package_list).startswith('error'):
        logger.error(archive_package_list)
        raise ArchivePakageException
    #更新应用的目标version
    with session_scope() as ss:
        for item in archive_package_list:
            application_name = item['application_name']
            target_version = item['target_version']
            ss.query(PublishApplication).filter(PublishApplication.publish_plan_id == publish_plan_id,
                                                PublishApplication.application_name == application_name).update(
                {
                    'target_version': target_version
                }, synchronize_session=False)
    with session_scope() as ss:
        # 2: 创建完成 更新publish plan  状态
        ss.query(PublishPlan).filter(PublishPlan.id == publish_plan_id).update({'status': 2}, synchronize_session=False)
