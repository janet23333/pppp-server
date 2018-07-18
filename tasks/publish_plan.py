import zipfile

import celery
import os
import requests
import shutil
from celery.utils.log import get_task_logger

from celery_worker import app
from common.error import InvalidUrlException, ArchivePackageException
from conf import settings
from orm.db import session_scope
from orm.models import PublishApplication, PublishPlan, PublishHost

logger = get_task_logger(__name__)

project_root_path = settings['project_root_path']


class CreatePlanTask(celery.Task):
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(
            'create plan success and taskid is {} ,retval is{} ,args is{}.kwargs id {}'.format(task_id, retval, args,
                                                                                               kwargs))
        with session_scope() as ss:
            # 创建完成 更新publish plan 状态
            publish_plan_id = kwargs['publish_plan_id']
            ss.query(PublishPlan).filter(PublishPlan.id == publish_plan_id).update({'status': 2},
                                                                                   synchronize_session=False)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        err_msg = 'create plan {0!r} failed: {1!r}'.format(task_id, exc)
        with session_scope() as ss:
            # 任务失败 更新publish plan 状态
            publish_plan_id = kwargs['publish_plan_id']
            ss.query(PublishPlan).filter(PublishPlan.id == publish_plan_id).update({'status': 3},
                                                                                   synchronize_session=False)
        # 任务失败时，把错误信息 打到log
        logger.error(err_msg)


@app.task(base=CreatePlanTask)
def down_load_and_archive_package(jenkins_url_list, inventory_version, publish_plan_id):
    # 以plan id 作为目录名称
    logger.info(publish_plan_id)
    package_path = '{}/release/{}'.format(project_root_path, publish_plan_id)
    if not os.path.exists(package_path):
        os.makedirs(package_path)

    index_path = '{}/index'.format(project_root_path)
    if not os.path.exists(index_path):
        os.makedirs(index_path)

    zip_path = '{}/zip'.format(package_path)
    if not os.path.exists(zip_path):
        os.makedirs(zip_path)

    # 把包下载到 release/plan_id/download 目录下
    for url in jenkins_url_list:
        file_name = url.split('/')[-1]
        save_file_path = '{}/{}'.format(zip_path, file_name)
        logger.info('save_file_path is {}'.format(save_file_path))
        r = requests.get(url)
        if r.status_code == 200:
            with open(save_file_path, 'wb') as _file:
                _file.write(r.content)
        else:
            logger.error('error {} {} download failed'.format(file_name, url))
            raise InvalidUrlException('{} error!!!'.format(url))

    # 把release目录下的zip包解压到archive目录下,然后进行move操作
    archive_path = '{}/archive'.format(package_path)
    if os.path.exists(archive_path):
        shutil.rmtree(archive_path, ignore_errors=True)
    os.makedirs(archive_path)
    for filename in os.listdir(zip_path):
        file_path = '{}/{}'.format(zip_path, filename)
        if zipfile.is_zipfile(file_path):
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(archive_path)
        else:
            raise ArchivePackageException('{}编译包不是zip包,请检查!'.format(file_path))

    # 从info文件中，读取commit_id和target_version。
    info_list = []
    for filename in os.listdir(archive_path):

        file_path = '{}/{}'.format(archive_path, filename)
        if filename.endswith('.info'):

            application_name = None
            commit_id = None
            target_version = None
            with open(file_path) as file:
                for line in file.readlines():
                    if line.startswith('APP-Package'):
                        artifacts_path = line[13:].strip()

                        if filename.endswith('.war.info'):
                            logger.info(artifacts_path)
                            name_version = artifacts_path[:-4].split('-')
                            target_version = '{}-{}'.format(name_version[-1], inventory_version)
                            application_name = '-'.join(name_version[:-1])
                        elif filename.endswith('bin.zip.info'):
                            name_version = artifacts_path[:-8].split('-')
                            target_version = '{}-{}'.format(name_version[-1], inventory_version)
                            application_name = '-'.join(name_version[:-1])

                        else:
                            raise ArchivePackageException('{} 文件错误,请检查!'.format(file_path))

                    if line.startswith('LAST-COMMIT-ID'):
                        commit_id = line[16:]
            if application_name is None or commit_id is None or target_version is None:
                raise ArchivePackageException('{} 文件错误,请检查!'.format(file_path))
            download_path = '{}/{}/{}'.format(project_root_path, application_name, target_version)
            os.makedirs(download_path, exist_ok=True)
            shutil.move(file_path, download_path)
            shutil.move(file_path.replace('.info', ''), download_path)
            info_list.append({
                'application_name': application_name,
                'target_version': target_version,
                'download_path': download_path,
                'commit_id': commit_id
            })
    # 根据info，生成index和rollback文件
    with open('{}/{}.index'.format(index_path, inventory_version), 'w') as index_file:
        for line in info_list:
            index_file.write('{} {} {}\n'.format(
                line['application_name'],
                line['target_version'],
                line['download_path']))
    with open('{}/{}_rollback.index'.format(index_path, inventory_version), 'w') as rollback_file:
        for line in info_list:
            application_name = line['application_name']
            with session_scope() as ss:
                host_list = ss.query(PublishHost.rollback_version).join(PublishApplication,
                                                                        PublishHost.publish_application_id == PublishApplication.id).filter(
                    PublishApplication.publish_plan_id == publish_plan_id,
                    PublishApplication.application_name == application_name).distinct(
                    PublishHost.rollback_version).all()
                if len(host_list) == 0:
                    warn_message = '# WARN! {} CMDB中无版本号，请检查！（新增模块忽略此提示）\n'.format(line['application_name'])
                    logger.warn(warn_message)
                    rollback_file.write(warn_message)

                elif len(host_list) > 1:
                    warn_message = 'WARN! {} 在CMDB中存在多个版本,请确认回滚版本！（注释掉错误的版本）\n'.format(line['application_name'])
                    logger.warn(warn_message)
                    rollback_file.write(warn_message)

                for host in host_list:
                    rollback_message = '{} {}\n'.format(line['application_name'], host[0])
                    rollback_file.write(rollback_message)

    # 更新应用的目标version
    with session_scope() as ss:
        for item in info_list:
            application_name = item['application_name']
            target_version = item['target_version']
            commit_id = item['commit_id']
            ss.query(PublishApplication).filter(PublishApplication.publish_plan_id == publish_plan_id,
                                                PublishApplication.application_name == application_name).update(
                {
                    'target_version': target_version,
                    'commit_id': commit_id
                }, synchronize_session=False)
    return publish_plan_id
