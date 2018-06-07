'''
    Utility module
'''
import subprocess
import base64
import functools
import hashlib
import json
import random
import re
import time
import uuid
from decimal import Decimal

import requests
import sqlalchemy
from sqlalchemy.ext import automap

from tornado.web import HTTPError
import os
from datetime import datetime
from datetime import date
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

KEY = base64.b64encode(
    uuid.uuid5(uuid.NAMESPACE_X500, 'bidong wifi').hex.encode('utf-8'))

b64encode = base64.b64encode
b64decode = base64.b64decode


def run_shell(cmd, timeout=300):
    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            shell=True)
        std_out, std_err = p.communicate(input=None, timeout=timeout)
        if p.returncode == 0:
            if std_out or std_err:
                return '{}'.format((std_out + std_err).decode('utf-8').rstrip('\n'))
            return '{} {}'.format(std_out, std_err)
        else:
            if std_err or std_out:
                return 'error msg : {}: {}'.format(cmd, (std_out + std_err).decode('utf-8').rstrip('\n'))
            return 'error msg : {}: {}'.format(cmd, std_out + std_err)
    except Exception as e:
        # log.error(e)
        return 'error Exception msg : {}: {}'.format(cmd, e)


class AlchemyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, tuple):
            data = {}
            for obj in o:
                data.update(self.parse_sqlalchemy_object(obj))
            return data
        if isinstance(o, automap.AutomapBase):
            return self.parse_sqlalchemy_object(o)
        return json.JSONEncoder.default(self, o)

    def parse_sqlalchemy_object(self, o):
        start = time.time()
        data = {}

        fields = o.__json__() if hasattr(o, '__json__') else dir(o)

        for field in [
                f for f in fields if not f.startswith('_')
                and f not in ['metadata', 'query', 'query_class']
                and hasattr(o.__getattribute__(f), '__call__') == False
        ]:
            value = o.__getattribute__(field)
            print("fileds:", field)
            try:
                json.dumps(value)
                data[field] = value
            except TypeError:
                data[field] = None
        print("parse_sqlalchemy_object in %ss" % (time.time() - start))
        return data


class MyJSONEncoder(json.JSONEncoder):
    '''
        serial datetime date
    '''

    def default(self, obj):
        '''
            serialize datetime & date
        '''
        if isinstance(obj, datetime):
            return obj.strftime(DATE_FORMAT)
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, sqlalchemy.engine.RowProxy):
            _dict = {}
            for key, value in obj.items():
                _dict.setdefault(key, value)
            return _dict
        elif isinstance(obj, sqlalchemy.orm.state.InstanceState):
            return
        else:
            # return super(json.JSONEncoder, self).default(obj)
            return super(MyJSONEncoder, self).default(obj)


json_encoder = MyJSONEncoder(ensure_ascii=False).encode
json_decoder = json.JSONDecoder().decode

# json_encoder = json.JSONEncoder().encode
# json_decoder = json.JSONDecoder().decode

# _PASSWORD_ = '23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNOPQRSTUVWXYZ~!@#$^&*<>=+-_'
_PASSWORD_ = '23456789'
_VERIFY_CODE_ = '23456789'

MAC_PATTERN = re.compile(r'[-:_]')

MOBILE_PATTERN = re.compile(
    r'^(?:13[0-9]|14[57]|15[0-35-9]|17[678]|18[0-9])\d{8}$')

NUM_PATTERN = re.compile(r'[0-9]')


def page_arguments_to_int(page):
    '''
    use only in parser page arguments
    :param page:
    :return:
    '''
    try:
        page = int(page)
        if page < 1:
            raise HTTPError(
                status_code=400,
                reason=
                "ValueError ,page &page_size arguments must be number and >0")
    except ValueError:
        raise HTTPError(
            status_code=400,
            reason=
            "ValueError ,page &page_size arguments  must be number and > 0")
    return page


def check_mobile(mobile):
    return True if re.match(MOBILE_PATTERN, mobile) else False


def check_num(num):
    return True if re.match(NUM_PATTERN, num) else False


def to_int(s):
    if isinstance(s, bytes):
        return int(s.decode())
    elif isinstance(s, str):
        return int(s)
    else:
        return s


def msg_send(MSG_URL, payload):
    """
    send mobile msg
    payload :  {mobile:'', msg:''}
    codes : utf8
    """
    header = {"Content-Type": "application/json "}
    r = requests.post(MSG_URL, data=json.dumps(payload), headers=header)
    data = json.loads(r.text)
    if data.get("Code") == 200:
        return True
    else:
        return False


def check_password(u_psw, q_psw):
    '''
        u_psw: user request password
        q_pwd: db saved password
        if password check pass, return False esle True
    '''
    un_equal = True
    if u_psw == q_psw or u_psw == md5(q_psw).hexdigest():
        un_equal = False
    return un_equal


def now(fmt=DATE_FORMAT, days=0, hours=0):
    _now = datetime.datetime.now()
    if days or hours:
        _now = _now + datetime.timedelta(days=days, hours=hours)
    return _now.strftime(fmt)


def cala_delta(start):
    '''
    '''
    _now = datetime.datetime.now()
    start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
    return (_now - start).seconds


def md5(*args):
    '''
        join args and calculate md5
        digest() : bytes
        hexdigest() : str
    '''
    md5 = hashlib.md5()
    md5.update(b''.join([
        item.encode('utf-8') if isinstance(item, str) else item
        for item in args
    ]))
    return md5


def sha1(*args):
    sha1 = hashlib.sha1()
    sha1.update(''.join(args).encode('utf-8'))
    return sha1


def sha256(*args):
    sha256 = hashlib.sha256()
    sha256.update(''.join(args).encode('utf-8'))
    return sha256


def generate_password(len=4):
    '''
        Generate password randomly
    '''
    return ''.join(random.sample(_PASSWORD_, len))


def generate_verify_code(_len=6):
    '''
        generate verify code
    '''
    return ''.join(random.sample(_VERIFY_CODE_, _len))


def token(user):
    '''
        as bidong's util module
    '''
    _now = int(time.time())
    _88hours_ago = _now - 3600 * 88
    _now, _88hours_ago = hex(_now)[2:], hex(_88hours_ago)[2:]
    data = ''.join([user, _88hours_ago])
    ret_data = uuid.uuid5(uuid.NAMESPACE_X500, data).hex
    return '|'.join([ret_data, _now])


def token2(user, _time):
    _t = int('0x' + _time, 16)
    _88hours_ago = hex(_t - 3600 * 88)[2:]
    data = ''.join([user, _88hours_ago])
    return uuid.uuid5(uuid.NAMESPACE_X500, data).hex


def format_mac(mac):
    '''
        output : ##:##:##:##:##:##
    '''
    mac = re.sub(r'[_.,; -]', ':', mac).upper()
    if 12 == len(mac):
        mac = ':'.join(
            [mac[:2], mac[2:4], mac[4:6], mac[6:8], mac[8:10], mac[10:]])
    elif 14 == len(mac):
        mac = ':'.join(
            [mac[:2], mac[2:4], mac[5:7], mac[7:9], mac[10:12], mac[12:14]])
    return mac


def strip_mac(mac):
    if mac:
        return re.sub(MAC_PATTERN, '', mac.upper())
    else:
        return ''


def _fix_key(key):
    '''
        Fix key length to 32 bytes
    '''
    slist = list(key)
    fixkeys = ('*', 'z', 'a', 'M', 'h', '.', '8', '0', 'O', '.', '.', 'a', '@',
               'v', '5', '5', 'k', 'v', 'O', '.', '*', 'z', 'a', 'r', 'h', '.',
               'x', 'k', 'O', '.', 'q', 'g')
    if len(key) < 32:
        pos = len(key)
        while pos < 32:
            slist.append(fixkeys[pos - len(key)])
            pos += 1
    if len(key) > 32:
        slist = slist[:32]
    return ''.join(slist)


def singleton(cls):
    ''' Use class as singleton. '''

    cls.__new_original__ = cls.__new__

    @functools.wraps(cls.__new__)
    def singleton_new(cls, *args, **kw):
        it = cls.__dict__.get('__it__')
        if it is not None:
            return it

        cls.__it__ = it = cls.__new_original__(cls, *args, **kw)
        it.__init_original__(*args, **kw)
        return it

    cls.__new__ = singleton_new
    cls.__init_original__ = cls.__init__
    cls.__init__ = object.__init__

    return cls


def ip_into_int(ip):
    # 先把 192.168.1.13 变成16进制的 c0.a8.01.0d ，再去了“.”后转成10进制的 3232235789 即可。
    # (((((192 * 256) + 168) * 256) + 1) * 256) + 13
    return functools.reduce(lambda x, y: (x << 8) + y, map(int, ip.split('.')))


def is_internal_ip(ip):
    ip = ip_into_int(ip)
    net_a = ip_into_int('10.255.255.255') >> 24
    net_b = ip_into_int('172.31.255.255') >> 20
    net_c = ip_into_int('192.168.255.255') >> 16
    return ip >> 24 == net_a or ip >> 20 == net_b or ip >> 16 == net_c


def timestampt2datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime(
        "%Y-%m-%d %H:%M:%S")


def dump_file(out_path, data_obj):
    with open(out_path, "w", encoding="UTF-8") as f_dump:
        json.dump(data_obj, f_dump, ensure_ascii=False)


def load_json_file(inpath):
    with open(inpath, "r", encoding="UTF-8") as f_dump:
        return json.load(f_dump)


def dump_file_ansible_inventory(content, file=None):
    from conf import settings
    if not file:
        file = str(datetime.now().strftime('%Y%m%d%H%M%S'))
    #save_path = '{}/inventory'.format(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    save_path = settings['inventory']
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    host = []
    for key, value in content.items():
        host.append('[{}]\n{}\n'.format(key, '\n'.join(value)))
    _content = '\n'.join(host)
    file_path = '{}/{}'.format(save_path, file)
    with open(file_path, 'w', encoding='UTF-8') as files:
        files.write(_content)
    return file_path


def take_out_unrightful_arguments(rightful_keys, arguments_dict):
    return {k: v for k, v in arguments_dict.items() if k in rightful_keys}


def pagination(query, page, page_size):
    return query[(page - 1) * page_size: page * page_size]


if __name__ == '__main__':
    print(timestampt2datetime(1515754157))

# if __name__ == '__main__':
#     _key = "CMDB!@#"
#     _kss = sha256(_key).hexdigest()
#     print(_kss, len(_kss))
