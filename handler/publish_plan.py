import json
from datetime import datetime
from json.decoder import JSONDecodeError

from celery import uuid
from sqlalchemy import desc

from common import util
from common.authentication import validate_requests, validate_user_permission
from common.error import PublishError
from common.util import take_out_unrightful_arguments
from handler.base import BaseHandler, HTTPError
from handler.base import BaseWebSocket
from orm.db import session_scope
from orm.field_map import application_type_map
from orm.field_map import publish_host_flag_map
from orm.models import PublishPattern, PublishPatternHost, PublishPatternTask
from orm.models import PublishPlan, PublishApplication, PublishHost
from tasks.log_task import audit_log
from tasks.publish_plan import down_load_and_archive_package
from worker.run_task import get_action_tasks

json_encoder = util.json_encoder


class PublishPlanHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('get')
    def get(self):
        rightful_keys = (
            'id',
            'title',
            'description',
            'inventory_version',
            'create_time',
            'update_time',
            'create_user',
            'status',
            'type',
            'page',
            'page_size',
        )

        uri_kwargs = take_out_unrightful_arguments(rightful_keys, self.url_arguments)

        page = int(uri_kwargs.pop("page", 1))
        page_size = int(uri_kwargs.pop("page_size", 5))

        with session_scope() as ss:
            publish_plan_query = ss.query(PublishPlan).filter_by(**uri_kwargs).filter(PublishPlan.status != 7).order_by(
                desc(PublishPlan.create_time))

            total_count = publish_plan_query.count()

            publish_plan_list = publish_plan_query[(page - 1) * page_size:page * page_size]

            res = [plan.to_dict() for plan in publish_plan_list]

        self.render_json_response(code=200, msg="OK", total_count=total_count, res=res)

    @validate_requests
    @validate_user_permission('post')
    def post(self):
        """
        add publish plan object
        argument should be list
        :return:
        """
        # task_id = uuid()
        user_id = self.user['id']
        arguments = self.body_arguments
        if not arguments:
            raise HTTPError(status_code=400, reason="json arguments is invalid")

        arguments.pop('id', None)
        application_list = arguments.pop('application_list')
        '''
        application_list argument example：
        [
            { 
                "application_name": "canyin",
                "application_type":1,
                "application_deploy_path":'xx/xx',
                "jenkins_url":'xxxx',
                "host_list":[
                    {
                        'host_name': 'xxx',
                        'host_ip': 'xxx',
                        "host_flag": 'master',
                        'rollback_version':''
                    }
                ]

            }
        ]
        '''
        # application_name_list = [url['application_name'] for url in application_list]
        jenkins_url_list = [url['jenkins_url'] for url in application_list]

        try:
            publish_pattern_list = arguments.pop('publish_pattern')
            """
            publish_pattern argument example:
            [
                {
                    'step': 1,
                    'title': 'title',
                    'note': 'note',
                    'action': 1,
                    'publish_host': [
                        {
                            'application_name': 'application_name',
                            'host_name': 'host_name'
                           
                        }
                    ]
                }
            ]
            """
        except KeyError:
            raise HTTPError(status_code=400, reason="publish_pattern argument is required")

        # 先创建 publish_plan
        inventory_version = str(datetime.now().strftime('%m%d%H%M'))
        with session_scope() as ss:
            publish_plan = PublishPlan()
            publish_plan.type = arguments.pop('type')
            publish_plan.title = arguments.pop('title')
            publish_plan.description = arguments.pop('description')
            publish_plan.create_user_id = user_id
            publish_plan.status = 1  # 正在创建发版
            publish_plan.inventory_version = inventory_version
            publish_plan.publish_project_id = arguments.pop('publish_project_id')
            ss.add(publish_plan)
            ss.flush()
            publish_plan_id = publish_plan.id

            #  创建publish application and publish host
            publish_application_dict = {}
            for application in application_list:
                application_name = application['application_name']
                if application_name:
                    application_type_num = application_type_map[application['application_type']]

                    publish_application = PublishApplication()
                    publish_application.application_name = application_name
                    publish_application.application_type = application_type_num
                    publish_application.jenkins_url = application['jenkins_url']
                    publish_application.publish_plan_id = publish_plan_id
                    publish_application.deploy_real_path = application['application_deploy_path']
                    # publish_application.target_version = target_version  后面update
                    ss.add(publish_application)
                    ss.flush()

                    #  创建 publish  host
                    host_dict = {}
                    for host_args in application['host_list']:
                        host_args.update({
                            'publish_application_id': publish_application.id,
                        })
                        host_args['host_flag'] = publish_host_flag_map[host_args['host_flag']]
                        publish_host = PublishHost(**host_args)
                        ss.add(publish_host)
                        ss.flush()
                        host_dict.update({
                            host_args['host_name']: publish_host.id
                        })

                    publish_application_dict.update({
                        application_name: {
                            "id": publish_application.id,
                            "type": application_type_num,
                            "hosts": host_dict
                        }
                    })

            # insert publish_pattern  and publish_pattern_host
            for pattern_dict in publish_pattern_list:
                publish_host_list = pattern_dict.pop('publish_host')

                # insert publish_pattern
                pattern = PublishPattern(**pattern_dict)
                pattern.publish_plan_id = publish_plan_id
                ss.add(pattern)
                ss.flush()
                pattern_id = pattern.id

                for publish_host_kwargs in publish_host_list:

                    pattern_application_name = publish_host_kwargs.pop('application_name')
                    host_name = publish_host_kwargs['host_name']
                    publish_host_id = publish_application_dict[pattern_application_name]['hosts'][host_name]

                    #  创建 PublishPatternHost
                    pattern_host = PublishPatternHost()
                    pattern_host.publish_host_id = publish_host_id
                    pattern_host.publish_pattern_id = pattern_id
                    ss.add(pattern_host)
                    ss.flush()

                    # insert publish_pattern_task
                    pattern_host_id = pattern_host.id
                    try:
                        tasks = get_action_tasks(
                            action=pattern_dict['action'],
                            application_type=publish_application_dict[pattern_application_name]["type"],
                            application_name=pattern_application_name
                        )
                    except PublishError as e:
                        raise HTTPError(status_code=400, reason=str(e))
                    ss.add_all(
                        [PublishPatternTask(publish_pattern_host_id=pattern_host_id, task_name=task) for task in tasks])
                    ss.flush()

        task_id = uuid()
        down_load_and_archive_package.apply_async(
            kwargs={'jenkins_url_list': jenkins_url_list, 'inventory_version': inventory_version,
                    'publish_plan_id': publish_plan_id}, task_id=task_id)
        audit_log(self, description='创建发版计划', resource_type=1, resource_id=publish_plan_id)

        self.render_json_response(code=200, msg="OK", publish_plan_id=publish_plan_id, task_id=task_id)

    @validate_requests
    @validate_user_permission('put')
    def put(self):
        """update publish plan"""

        res = {}
        arguments = self.body_arguments
        if not arguments:
            raise HTTPError(status_code=400, reason="json arguments is invalid")

        _id = arguments.pop("id", None)
        if not _id:
            raise HTTPError(status_code=400, reason="ID is required")

        with session_scope() as ss:
            q = ss.query(PublishPlan).filter_by(id=_id)
            q.update(arguments)

            db_res = q.one_or_none()
            if db_res:
                res = db_res.to_dict()

        audit_log(self, description='更新发版计划', resource_type=1, resource_id=_id)
        self.render_json_response(code=200, msg="OK", id=_id, res=res)

    @validate_requests
    @validate_user_permission('delete')
    def delete(self):
        """ delete publish plan by id"""

        arguments = self.body_arguments
        if not arguments:
            raise HTTPError(status_code=400, reason="json arguments is invalid")

        _id = arguments.pop("id", None)
        if not _id:
            raise HTTPError(status_code=400, reason="ID is required")

        with session_scope() as ss:
            ss.query(PublishPlan).filter_by(id=_id).update({'is_delete': 1})

        audit_log(self, description='删除发版计划', resource_type=1, resource_id=_id)
        self.render_json_response(code=200, msg='ok', res={'id': _id})


class PlanDetailHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('get')
    def get(self):
        plan_id = self.url_arguments.get('planId')
        with session_scope() as ss:
            plan = ss.query(PublishPlan).get(plan_id)

            if plan is not None:
                res = plan.to_dict()
                self.render_json_response(code=200, msg="OK", total_count=1, res=res)
            else:
                self.render_json_response(code=200, msg="OK", total_count=0, res={})


class PublishPlanWebSocket(BaseWebSocket):
    def on_message(self, message):
        """
        :param message:  { publish_plan_id :[]}
        :return:
        """
        super().on_message(message)
        try:
            message = json.loads(message)
            self.message = message
            self.current_status = []

            if 'publish_plan_ids' not in message or not isinstance(message['publish_plan_ids'], list):
                self.render_json_response(code=400, msg='Error ',
                                          res='Invalid arguments ,arguments should be like {}'.format(
                                              {'publish_plan_ids': []}))
                self.close()

        except JSONDecodeError:
            self.render_json_response(code=400, msg='Request arguments format error', res=message)
        except Exception:
            self.render_json_response(code=400, msg='Unknown error on message', res=message)

    def callback(self):
        if self.message is None or len(self.message['publish_plan_ids']) < 1:
            return
        with session_scope() as ss:
            publish_plan_ids = self.message['publish_plan_ids']
            publish_plans = ss.query(PublishPlan).filter(PublishPlan.id.in_(publish_plan_ids)).order_by(
                PublishPlan.id).all()

            new_status = [i.status for i in publish_plans]
            if new_status != self.current_status:
                res = [publish_plan.to_dict() for publish_plan in publish_plans]
                self.render_json_response(res)

            self.current_status = [i.status for i in publish_plans]


class PlanRetryHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('post')
    def post(self):
        '''
        创建发版任务失败后，重试 下载与解压
        :return:
        '''
        argument = self.body_arguments
        publish_plan_id = argument.pop('publish_plan_id', None)
        if publish_plan_id is None:
            raise HTTPError(status_code=400, reason="Missing argument:publish_plan_id")

        with session_scope() as ss:
            plan = ss.query(PublishPlan).filter_by(id=publish_plan_id, status=3).one_or_none()
            if plan is None:
                raise HTTPError(status_code=400, reason="查找的publish_plan_id: {} 不存在，或者已创建成功 ".format(publish_plan_id))
            # 状态重置为创建中
            plan.status = 1
            ss.flush()
            inventory_version = plan.inventory_version
            jenkins_url_list = [app.jenkins_url for app in plan.application_list]

            task_id = uuid()
            down_load_and_archive_package.apply_async(
                kwargs={'jenkins_url_list': jenkins_url_list, 'inventory_version': inventory_version,
                        'publish_plan_id': publish_plan_id},
                task_id=task_id)
        audit_log(self, description='重试发版计划', resource_type=1, resource_id=publish_plan_id)
        self.render_json_response(code=200, msg="OK", publish_plan_id=publish_plan_id, task_id=task_id)

    @validate_requests
    @validate_user_permission('put')
    def put(self, *args, **kwargs):
        '''
        修改应用包地址
        :param args:
        :param kwargs:
        :return:
        '''
        argument = self.body_arguments
        publish_plan_id = argument.pop('publish_plan_id', None)
        application_argus = argument.pop('applications', None)
        if publish_plan_id is None:
            raise HTTPError(status_code=400, reason="Missing argument:publish_plan_id")
        # new_inventory_version = str(datetime.now().strftime('%m%d%H%M'))

        jenkins_url_list = []
        with session_scope() as ss:
            # update publish plan
            publish_plan = ss.query(PublishPlan).filter_by(id=publish_plan_id).one_or_none()
            if publish_plan is None:
                raise HTTPError(status_code=400, reason="查找的publish_plan_id: {} 不存在 ".format(publish_plan_id))

            # publish_plan.inventory_version = new_inventory_version
            inventory_version = publish_plan.inventory_version
            # 状态重置为创建中
            publish_plan.status = 1
            ss.flush()

            # update publish application
            for app_dict in application_argus:
                publish_application_id = app_dict.pop('publish_application_id')
                jenkins_url_list.append(app_dict['jenkins_url'])

                q = ss.query(PublishApplication).filter_by(id=publish_application_id)
                q.update(app_dict)

            task_id = uuid()
            down_load_and_archive_package.apply_async(
                kwargs={'jenkins_url_list': jenkins_url_list,
                        'inventory_version': inventory_version,
                        'publish_plan_id': publish_plan_id},
                task_id=task_id)

        audit_log(self, description='修改应用包地址', resource_type=1, resource_id=publish_plan_id)
        self.render_json_response(code=200, msg="OK", publish_plan_id=publish_plan_id, task_id=task_id)
