from ldap3 import Server, Connection, SUBTREE, SIMPLE
from ldap3.core.exceptions import LDAPInvalidCredentialsResult
from tornado.log import app_log

from conf import settings

configs = settings['ldap']

dict_map = {

    'mobile': 'phone',
    'cn': 'username',
    'displayName': 'fullname',
    'mail': 'email'

}


def _init_connect():
    ldap_server = configs['ldap_server']
    user = configs['user']
    port = int(configs['port'])
    password = configs['password']

    server = Server(ldap_server, port=port, use_ssl=False, tls=False)
    conn = Connection(server, user=user, password=password, authentication=SIMPLE, raise_exceptions=True,
                      auto_bind=True)
    return conn


def _search_by_name(conn, username):
    search_base = configs['baseDN']
    if conn.search(search_base=search_base,
                   search_filter='(cn=' + username + ')',
                   search_scope=SUBTREE,
                   attributes=dict_map.keys(),
                   paged_size=10000):

        entry = conn.entries[0]  # 用户名全局唯一，因此至多找到一个用户

        user_dn = entry.entry_dn  # user_dn

        user_info = {}

        for attr, value in entry.entry_attributes_as_dict.items():  # use_info 的属性
            user_info.update({dict_map[attr]: value[0]})

        group = [i for i in user_dn.split(',') if i.startswith('ou=') and i.endswith('部')]  # user的部门信息

        if group:
            dep_list = []
            group = group[0].split('=')[1]
            dep_list.append(group)
            user_info.update({'department_name': dep_list})

        return user_dn, user_info
    else:
        error = 'user({username}) is not exist'.format(username=username)
        app_log.error(error)
        return None, None


def _valid_user(conn, user_dn, password):
    if user_dn:
        # Bind again with another user
        try:
            if conn.rebind(user=user_dn, password=password):
                return True
        except LDAPInvalidCredentialsResult:
            error = 'user({user_dn}) valid error'.format(user_dn=user_dn)
            app_log.error(error)
    return False


def search_user(username):
    """
    根据用户名，搜索用户
    :param username: 用户名
    :return: 返回用户信息。如果用户不存在，返回 None
    """
    conn = _init_connect()

    user_dn, info = _search_by_name(conn, username)

    conn.unbind()

    return info


def valid_user(username, password):
    """
    验证用户
    :param username: 用户名
    :param password: 用户密码
    :return: 验证通过，返回 user info；验证失败，返回 NOne
    """
    conn = _init_connect()
    error_reason = ''
    is_valid = False
    # 需要先根据username获得user_dn
    user_dn, info = _search_by_name(conn, username)
    if user_dn:
        # 再验证用户的密码
        is_valid = _valid_user(conn, user_dn, password)
        if not is_valid:
            error_reason = 'password error'
    else:
        error_reason = "user error"
    conn.unbind()

    return (info, error_reason) if is_valid else (None, error_reason)
