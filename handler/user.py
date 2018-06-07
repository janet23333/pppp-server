from common.authentication import validate_requests, validate_user_permission
from handler.base import BaseHandler, HTTPError
from orm.db import session_scope
from orm.models import User, Department


class UserHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('get')
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 15))

        argus = self.url_arguments
        name = argus.pop('name', None)
        department_id = argus.pop('department_id', None)
        with session_scope() as ss:
            user_query = ss.query(User)
            if name:
                user_query = user_query.filter(User.name == name)
            if department_id:
                user_query = user_query.filter(Department.id == department_id)

            total_count = user_query.count()

            user_list = user_query[(page - 1) * page_size:page * page_size]

            res = [user.to_dict() for user in user_list]

        self.render_json_response(code=200, msg="OK", total_count=total_count, res=res)

    @validate_requests
    @validate_user_permission('post')
    def post(self):
        """
        add user  object
        argument should be list
        :return:
        """
        arguments = self.body_arguments
        if not arguments:
            raise HTTPError(status_code=400, reason="json arguments is invalid")
        arguments.pop('id', None)
        with session_scope() as ss:
            user_instance = User(arguments)

            ss.add(user_instance)

            ss.flush()
            _id = user_instance.id

            res = ss.query(User).get(_id).to_dict()
        self.render_json_response(code=200, msg="OK", id=_id, res=res)

    @validate_requests
    @validate_user_permission('put')
    def put(self):
        """update user"""

        arguments = self.body_arguments
        if not arguments:
            raise HTTPError(status_code=400, reason="json arguments is invalid")

        _id = arguments.pop("id", None)
        if not _id:
            raise HTTPError(status_code=400, reason="ID is required")
        with session_scope() as ss:
            ss.query(User).get(_id).update(arguments)

            res = ss.query(User).get(_id).to_dict()
        self.render_json_response(code=200, msg="OK", id=_id, res=res)

    @validate_requests
    @validate_user_permission('delete')
    def delete(self):
        """ delete user by id"""

        arguments = self.body_arguments
        if not arguments:
            raise HTTPError(status_code=400, reason="json arguments is invalid")

        _id = arguments.pop("id", None)
        if not _id:
            raise HTTPError(status_code=400, reason="ID is required")
        with session_scope() as ss:
            ss.query(User).get(_id).delete()
        self.render_json_response(code=200, msg="OK")
