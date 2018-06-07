import unittest
import requests
from orm import db
from conf import settings


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.baseurl = 'http://10.10.50.30:%s/api' % settings['server']['port']
        self.session = requests.Session()
        self.session.headers[
            'token'] = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6NSwiZnVsbG5hbWUiOiJcdTllYzRcdTYwMWRcdTk0ZWQiLCJ1c2VybmFtZSI6Imh1YW5nc2ltaW5nIiwiZW1haWwiOiJodWFuZ3NpbWluZ0B5dW5uZXguY29tIiwiY3JlYXRlX3RpbWUiOiIyMDE4LTA0LTEyIDExOjEwOjM4IiwidXBkYXRlX3RpbWUiOiIyMDE4LTA0LTEyIDExOjEwOjM4IiwiZGVwYXJ0bWVudF9uYW1lIjoiXHU4ZmQwXHU3ZWY0XHU1ZGU1XHU3YTBiXHU5MGU4In0.XQYJllSAMMxmRTU-QQPDuPmyO4MqfXq7J_3AmvGale4'
        self.db_session = db.SESSION_MAKER()

    def tearDown(self):
        if self.session:
            self.session.close()

        if self.db_session:
            self.db_session.close()
