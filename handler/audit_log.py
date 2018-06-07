from handler.base import BaseHandler
from orm.db import session_scope
from orm.models import AuditLog
from common.util import take_out_unrightful_arguments, pagination
from sqlalchemy import desc


class AuditLogHandler(BaseHandler):
    def get(self):
        # take args
        rightful_keys = ('id', 'create_time', 'update_time', 'user_id', 'resource_type', 'resource_id', 'description',
                         'visible', 'method', 'path', 'fullpath', 'body', 'page', 'page_size', 'order_by', 'desc',
                         'between_time', 'return_resource')
        uri_kwargs = take_out_unrightful_arguments(rightful_keys, self.url_arguments)

        page = int(uri_kwargs.pop("page", 1))
        page_size = int(uri_kwargs.pop("page_size", 15))

        order_by = uri_kwargs.pop('order_by', None)
        try:
            desc_ = int(uri_kwargs.pop('desc', 0))
        except ValueError:
            desc_ = 0

        try:
            return_resource = int(uri_kwargs.pop('return_resource', 0))
        except ValueError:
            return_resource = 0

        between_time = uri_kwargs.pop('between_time', None)
        if between_time is not None:
            uri_kwargs.pop('create_time', None)
            between_time = between_time.split(',')
            if len(between_time) < 2:
                self.render_json_response(code=400, msg='between_time need 2 arguments', res=[])

        with session_scope() as ss:
            # join sql
            q = ss.query(AuditLog).filter_by(**uri_kwargs)

            if between_time:
                q = q.filter(AuditLog.create_time.between(between_time[0], between_time[1]))

            if order_by is not None:
                if desc_:
                    order_by = desc(order_by)
                q = q.order_by(order_by)

            total_count = q.count()

            res = pagination(q, page, page_size)
            res = [r.to_dict(return_resource) for r in res]

        return self.render_json_response(code=200, msg='ok', total_count=total_count, res=res)
