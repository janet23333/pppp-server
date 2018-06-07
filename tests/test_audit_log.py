from tests.base import BaseTestCase
import unittest
from orm.models import AuditLog
from orm import db
import time


class AuditLogTestCase(BaseTestCase):
    def test_audit(self):
        url = self.baseurl + '/publish_plan'
        data = {
            "type":
                0,
            "application_list": [{
                "application_name":
                    "saofu-mod-card",
                "jenkins_url":
                    "http://git.ops.yunnex.com/deployment/packages/raw/21169a5f27f03f2aa357720a966d15765683a6fc/saofu-mod-card.zip"
            }, {
                "application_name":
                    "saofu-mobile",
                "jenkins_url":
                    "http://git.ops.yunnex.com/deployment/packages/raw/5d20894d6b604d493dc5046bcf1ce944018ea8a4/saofu-mobile.zip"
            }],
            "description":
                "test"
        }

        result = self.session.post(url, json=data)
        _id = result.json()['id']
        time.sleep(3)
        audit = self.db_session.query(AuditLog).filter_by(resource_id=_id, resource_type=1).first()
        self.assertEqual(audit.resource_type, 1, audit.resource_type)
        self.assertEqual(audit.resource_id, _id, audit.resource_id)
        self.assertEqual(audit.description, '创建发版计划', audit.description)
        self.assertEqual(audit.method, 'POST', audit.method)
        self.assertEqual(audit.path, '/api/publish_plan', audit.path)

        result = self.session.delete(url, json={'id': _id})
        time.sleep(3)
        self.db_session = db.SESSION_MAKER()
        audit = self.db_session.query(AuditLog).filter_by(resource_id=_id, resource_type=1).all()[-1]
        self.assertEqual(audit.resource_type, 1, audit.resource_type)
        self.assertEqual(audit.resource_id, _id, audit.resource_id)
        self.assertEqual(audit.description, '删除发版计划', audit.description)
        self.assertEqual(audit.method, 'DELETE', audit.method)
        self.assertEqual(audit.path, '/api/publish_plan', audit.path)

    def test_audit_get_handler_format(self):
        url = self.baseurl + '/audit_log'
        params = {'id': 1}
        keys = ('id', 'create_time', 'update_time', 'user_id', 'resource_type', 'resource_id', 'description', 'visible',
                'method', 'path', 'fullpath', 'body', 'user')

        response = self.session.get(url, params=params)
        self.assertEqual(response.status_code, 200, response.status_code)
        result = response.json()
        self.assertTrue('res' in result)
        self.assertTrue('total_count' in result)
        result = result['res']
        self.assertIsInstance(result, list, result)
        for log in result:
            for k in log:
                self.assertTrue(k in keys, [k, keys])
            break
        self.assertEqual(result[0]['id'], params['id'], result)

    def test_audit_get_handler_unrightful_arg(self):
        url = self.baseurl + '/audit_log'
        params = {'iiiid': 1}
        response = self.session.get(url, params=params)
        self.assertEqual(response.status_code, 200, response.status_code)

    def test_audit_get_handler_arguments(self):
        url = self.baseurl + '/audit_log'
        params = {'order_by': 'id', 'desc': 1, 'page_size': 20, 'return_resource': 1}
        response = self.session.get(url, params=params)
        self.assertEqual(response.status_code, 200, response.status_code)
        result = response.json()['res']
        self.assertTrue('resource' in result[0], result[0])
        self.assertEqual(len(result), params['page_size'], len(result))
        self.assertTrue(result[0]['id'] > 1, result[0][params['order_by']])

    def test_audit_get_handler_between_time(self):
        url = self.baseurl + '/audit_log'
        params = {'between_time': '2018-04-18,2018-04-18'}
        response = self.session.get(url, params=params)
        self.assertEqual(response.status_code, 200, response.status_code)
        result = response.json()['res']
        for log in result:
            create_time = log['create_time']
            self.assertTrue('2018-04-18' in create_time, create_time)


if __name__ == '__main__':
    unittest.main()
