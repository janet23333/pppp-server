import json

import celery
from billiard.einfo import ExceptionInfo
from celery.utils.log import get_task_logger
from celery.utils.serialization import get_pickleable_exception, get_pickleable_etype

from orm.db import session_scope
from orm.models import PublishTask
from worker.pattern import upgrade_pattern_status
from worker.pattern_host import upgrade_pattern_host_status
from worker.pattern_task import upgrade_pattern_task_status
from datetime import datetime

logger = get_task_logger(__name__)


class AnsibleError(Exception):
    pass


class TaskError(Exception):
    pass


class BaseTask(celery.Task):
    def do_success(self, retval, task_id, args, kwargs):
        raise NotImplementedError('Tasks must define the do_success method.')

    def on_success(self, retval, task_id, args, kwargs):
        try:
            logger.info(
                'my task success and taskid is {} ,retval is{} ,args is{}.kwargs id {}'.format(task_id, retval, args,
                                                                                               kwargs))
            # 如果执行成功，且有下一步，则执行下一步
            if self.do_success(retval, task_id, args, kwargs) and kwargs.get('next_task_kwargs'):
                for next_task_kwarg in kwargs['next_task_kwargs']:
                    with session_scope() as ss:
                        from worker.run_task import run_celery_task
                        run_celery_task(session=ss, **next_task_kwarg)

        except Exception as e:
            einfo = ExceptionInfo()
            einfo.exception = get_pickleable_exception(einfo.exception)
            einfo.type = get_pickleable_etype(einfo.type)
            self.on_failure(e, task_id, args, kwargs, einfo)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        argus = {"status": "FAILED", "result": str(exc), "end_time": datetime.now()}

        with session_scope() as ss:
            publish_task = ss.query(PublishTask).filter(PublishTask.celery_task_id == task_id).one_or_none()

            if publish_task is None:
                logger.error('PublishTask {} is not exist!'.format(task_id))
            else:
                for k, v in argus.items():
                    publish_task.__setattr__(k, v)
                ss.flush()

                pattern_task_id = publish_task.publish_pattern_task_id

                if pattern_task_id != 0:
                    pattern_task = upgrade_pattern_task_status(ss, pattern_task_id, argus['status'])

                    pattern_host_id = pattern_task.publish_pattern_host_id
                    pattern_hosts = upgrade_pattern_host_status(ss, pattern_host_id)

                    pattern_id = pattern_hosts[0].publish_pattern_id
                    upgrade_pattern_status(ss, pattern_id)


class AnsibleTask(BaseTask):

    @staticmethod
    def get_ansible_result(result):
        # TODO:
        # start/delta/end time  no result return
        success_result = result.get('success')
        failed_result = result.get("failed")
        unreachable_result = result.get('unreachable')

        if success_result:
            result = success_result
        elif failed_result:
            result = failed_result
        elif unreachable_result:
            result = unreachable_result
        else:
            result = {}

        if len(result.keys()) > 1:
            raise AnsibleError("an ansible task with {} hosts".format(len(result.keys())))

        host = list(result.keys())[0]
        result = result[host]

        return result

    def do_success(self, retval, task_id, args, kwargs):
        with session_scope() as ss:
            publish_task = ss.query(PublishTask).filter(PublishTask.celery_task_id == task_id).one_or_none()
            if publish_task is None:
                raise TaskError('PublishTask {} is not exist!'.format(task_id))
            else:
                ansible_result = self.get_ansible_result(retval)
                if ansible_result.get('rc') == 0:
                    ansible_status = 'SUCCESS'
                else:
                    ansible_status = 'FAILED'

                publish_task.status = ansible_status
                publish_task.end_time = datetime.now()
                try:
                    publish_task.result = json.dumps(ansible_result)
                except json.JSONDecodeError:
                    publish_task.result = ansible_result
                ss.flush()

                pattern_task_id = publish_task.publish_pattern_task_id
                if pattern_task_id != 0:
                    pattern_task = upgrade_pattern_task_status(ss, pattern_task_id, ansible_status)

                    pattern_host_id = pattern_task.publish_pattern_host_id
                    pattern_hosts = upgrade_pattern_host_status(ss, pattern_host_id)

                    pattern_id = pattern_hosts[0].publish_pattern_id
                    upgrade_pattern_status(ss, pattern_id)

                if ansible_status == 'SUCCESS':
                    return True


class DubboTask(BaseTask):

    def do_success(self, retval, task_id, args, kwargs):

        argus = {"status": "SUCCESS", "result": json.dumps(retval) if retval else None, "end_time": datetime.now()}
        with session_scope() as ss:

            publish_task = ss.query(PublishTask).filter(PublishTask.celery_task_id == task_id).one_or_none()
            if publish_task is None:
                raise TaskError('PublishTask {} is not exist!'.format(task_id))
            else:

                for k, v in argus.items():
                    publish_task.__setattr__(k, v)
                ss.flush()

                pattern_task_id = publish_task.publish_pattern_task_id
                if pattern_task_id != 0:
                    pattern_task = upgrade_pattern_task_status(ss, pattern_task_id, argus['status'])

                    pattern_host_id = pattern_task.publish_pattern_host_id
                    pattern_hosts = upgrade_pattern_host_status(ss, pattern_host_id)

                    pattern_id = pattern_hosts[0].publish_pattern_id
                    upgrade_pattern_status(ss, pattern_id)

            return True


class CheckTask(BaseTask):

    def do_success(self, retval, task_id, args, kwargs):
        # 有返回值，执行下一步；没有，则停止
        return True if retval else False
