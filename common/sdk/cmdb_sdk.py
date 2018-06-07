#!/usr/bin/python
# coding: utf8


from __future__ import print_function

from urllib import parse

import requests


class CmdbSdkException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class CmdbSdk(object):
    def __init__(self, host, scheme="http", user=None, passwd=None, token=None):
        self.url = host + '/'
        if not host.startswith('http'):
            self.url = scheme + '://' + self.url
        self.headers = {'Content-Type': 'application/json',
                        'User-Agent': 'python/cmdb_sdk'}
        self.login(username=user, password=passwd, token=token)

    def login(self, username=None, password=None, token=None):
        if (username and password) is not None:
            _token = self.post('token', username=username, password=password)
        else:
            if token:
                _token = token
            else:
                raise CmdbSdk("login() takes exactly argument (username and password) or (token)")
        self.headers["token"] = _token

    def get(self, method, property_id=None, response_obj=False, **kwargs):
        url = parse.urljoin(self.url, method)
        if property_id is not None:
            url = parse.urljoin(url + '/', str(property_id))
        for k, v in kwargs.items():
            if v and isinstance(v, (tuple, list)):
                kwargs[k] = ",".join(v)
        res = requests.get(url, params=kwargs, headers=self.headers)
        # print(res.url)
        if response_obj:
            return res
        res = res.json()
        if res['code'] != 200:
            raise CmdbSdk(res['msg'])
        return res['res']

    def post(self, method, response_obj=False, **kwargs):
        url = parse.urljoin(self.url, method)
        res = requests.post(url, data=kwargs, headers=self.headers)
        if response_obj:
            return res
        res = res.json()
        if res['code'] != 200:
            raise CmdbSdk(res['msg'])
        return res['res']
