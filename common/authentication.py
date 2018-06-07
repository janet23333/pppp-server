import jwt
from jwt import InvalidTokenError
from tornado.log import app_log

from conf import settings
from tornado.web import HTTPError


def validate_requests(func):
    """
     验证用户回传的token,监测是否有权限，
     同时把token里的user 信息写进self.request.arguments
     装饰器函数
    """

    def _deco(*args, **kwargs):
        _self = args[0]
        token = _self.get_query_argument('token', None)  # from url
        if not token:
            headers = _self.request.headers  # from headers
            token = headers["Token"] if "Token" in headers.keys() else None
        if not token:
            raise HTTPError(status_code=401, reason="Unauthorized,Missing token")
        try:
            payload = jwt.decode(token, settings['token_secret'], algorithms=['HS256'])
            app_log.info(payload)
            _self.payload = payload

            return func(*args, **kwargs)

        except InvalidTokenError as e:
            raise HTTPError(status_code=401, reason=str(e))

    return _deco


def validate_user_permission(http_req_method):
    """
        根据用户的角色归属，验证用户对数据库的增删改查权限

        用户的角色可归属于dev，ops，admin，权限如下
                dev | ops | admin
        get      √     √      √
        put      ×     √      √
        post     ×     √      √
        delete   ×     ×      √

    """

    def _validate_user_permission(func):
        def _deco(*args, **kwargs):
            role_method_map = {'dev': {'get': True, 'put': True, 'post': False, 'delete': False},
                               'ops': {'get': True, 'put': True, 'post': True, 'delete': True}
                               }
            _self = args[0]
            department_list = _self.payload.get('department_name')

            if department_list and '运维工程部' in department_list:
                role = 'ops'
            else:
                role = 'dev'
            if role is None:
                raise HTTPError(status_code=403, reason='not found role')

            if role not in role_method_map:
                raise HTTPError(status_code=403, reason='incorrect role: {}'.format(role))

            if not role_method_map[role][http_req_method]:
                raise HTTPError(status_code=403, reason='not allow role[{}] '
                                                        'to use http req method[{}]'.format(role, http_req_method))
            func(*args, **kwargs)

        return _deco

    return _validate_user_permission
