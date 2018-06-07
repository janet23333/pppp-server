import jwt
from ldap3.core.exceptions import LDAPException
from tornado.log import app_log

from common import ldap
from conf import settings
from orm.db import session_scope
from orm.models import Department, User, UserDepartment
from .base import BaseHandler, HTTPError


class TokenHandler(BaseHandler):
    def post(self):
        """
        用户登录,获取token
        """

        username = self.body_arguments.get('username')
        password = self.body_arguments.get('password')

        if not username or not password:
            raise HTTPError(status_code=400, reason='Missing arguments,please check  your username & password')

        try:
            user, error_reason = ldap.valid_user(username, password)
        except LDAPException as e:
            app_log.error(e)
            raise HTTPError(status_code=500, reason='ldap error')

        if not user:
            raise HTTPError(status_code=400, reason=error_reason)

        # update info
        with session_scope() as ss:
            # update user
            user_instance = ss.query(User).filter(User.username == user['username']).one_or_none()
            if not user_instance:
                user_instance = User()
                ss.add(user_instance)
            user_instance.username = user['username']
            user_instance.fullname = user['fullname']
            user_instance.email = user['email']
            ss.flush()
            # update department
            department = user.pop('department_name', None)
            # delete old user-department
            ss.query(UserDepartment).filter(UserDepartment.user_id == user_instance.id).delete()
            if department is not None:
                for dep_name in department:
                    department_instance = ss.query(Department).filter(Department.name == dep_name).one_or_none()
                    if not department_instance:
                        department_instance = Department(name=dep_name)
                        ss.add(department_instance)
                        ss.flush()
                    ud = UserDepartment()
                    ud.department_id = department_instance.id
                    ud.user_id = user_instance.id
                    ss.add(ud)
                    ss.flush()
            token = jwt.encode(payload=user_instance.to_dict(), key=settings['token_secret'], algorithm='HS256').decode("utf-8")

        self.render_json_response(code=200, msg='OK', res={'token': token})
