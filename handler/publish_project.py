from handler.base import BaseHandler, HTTPError
from common.authentication import validate_requests, validate_user_permission
from orm.models import PublishProject
from orm.db import session_scope
from common.util import take_out_unrightful_arguments, pagination
from sqlalchemy import desc
from tasks.log_task import audit_log


class PublishProjectHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('post')
    def post(self):
        try:
            project_name = self.body_arguments.pop('name')
        except KeyError:
            raise HTTPError(status_code=400, reason="Missing argument 'name'")

        with session_scope() as ss:
            publish_project = PublishProject()
            publish_project.name = project_name
            publish_project.create_user_id = self.user['id']
            ss.add(publish_project)
            ss.flush()
            res = publish_project.to_dict()
            project_id = res['id']

        audit_log(self, description='创建发版项目', resource_type=5, resource_id=project_id)
        self.render_json_response(code=200, res=res, id=project_id)

    @validate_requests
    @validate_user_permission('get')
    def get(self):
        rightful_keys = (
            'id',
            'create_time',
            'update_time',
            'page',
            'page_size',
            'order_by',
            'desc',
            'name',
            'status',
            'return_resource',
            'is_delete',
            'create_user_id',
        )
        uri_kwargs = take_out_unrightful_arguments(rightful_keys, self.url_arguments)
        page = int(uri_kwargs.pop("page", 1))
        page_size = int(uri_kwargs.pop("page_size", 15))
        order_by = uri_kwargs.pop("order_by", None)
        try:
            desc_ = int(uri_kwargs.pop('desc', 0))
        except ValueError:
            desc_ = 0

        try:
            _return_resource = int(uri_kwargs.pop('return_resource', 0))
        except ValueError:
            _return_resource = 0

        with session_scope() as ss:
            q = ss.query(PublishProject).filter_by(**uri_kwargs)
            if order_by is not None:
                if desc_:
                    order_by = desc(order_by)
                q = q.order_by(order_by)
            total_count = q.count()
            db_res = pagination(q, page, page_size)
            res = [r.to_dict(_return_resource) for r in db_res]

        self.render_json_response(code=200, total_count=total_count, res=res)

    @validate_requests
    @validate_user_permission('put')
    def put(self):
        res = {}
        rightful_keys = (
            'id',
            'name',
            'status',
            'is_delete',
        )
        body_kwargs = take_out_unrightful_arguments(rightful_keys, self.body_arguments)

        id_ = body_kwargs.pop('id', None)
        if id_ is None:
            raise HTTPError(status_code=400, reason='Missing argument "id"')

        with session_scope() as ss:
            q = ss.query(PublishProject).filter_by(id=id_)
            q.update(body_kwargs)

            db_res = q.one_or_none()
            if db_res is not None:
                res = db_res.to_dict()

        audit_log(self, description='更新发版项目', resource_type=5, resource_id=id_)
        self.render_json_response(code=200, res=res)

    @validate_requests
    @validate_user_permission('delete')
    def delete(self):
        _id = self.body_arguments.pop('id', None)
        if _id is None:
            raise HTTPError(status_code=400, reason='Missing argument "id"')

        with session_scope() as ss:
            ss.query(PublishProject).filter_by(id=_id).update({'is_delete': 1})

        audit_log(self, description='删除发版项目', resource_type=5, resource_id=_id)
        self.render_json_response(code=200, id=_id, res={'id': _id})
