from tests.base import BaseTestCase
from orm.models import PublishPattern, PublishPatternHost


class PublishPlanTestCase(BaseTestCase):
    def setUp(self):
        super(PublishPlanTestCase, self).setUp()
        self.url = self.baseurl + '/publish_plan'

    def test_create_plan_pattern(self):
        payload = {
            'type': 1,
            'title': 'I am test plan title',
            'description': 'I am test plan description',
            'application_list': [
                {
                    'application_name': 'linesvr-mod-service',
                    'jenkins_url': 'http://git.ops.yunnex.com/deployment/packages/raw/9ba23a84118e12d428834a69dc48d0d450b8f11e/linesvr-mod-service.zip',
                },
                {
                    'application_name': 'linesvr-web-mobile',
                    'jenkins_url': 'http://git.ops.yunnex.com/deployment/packages/raw/66faef5982668e7b03cf4fd12f61e51df9ad28a2/linesvr-web-mobile.zip',
                },
            ],
            'publish_pattern': [
                {
                    'step': 1,
                    'title': '部署master主机linesvr-mod-service服务',
                    'note': 'test note',
                    'action': 1,
                    'publish_host': [
                        {
                            'application_name': 'linesvr-mod-service',
                            'host_name': 'UGZB-TEST-M2-001',
                            'host_flag': 'master',
                        },
                    ]
                },
                {
                    'step': 2,
                    'title': '停slave主机linesvr-mod-service服务',
                    'note': 'test note',
                    'action': 2,
                    'publish_host': [
                        {
                            'application_name': 'linesvr-mod-service',
                            'host_name': 'UGZB-TEST-M2-002',
                            'host_flag': 'slave',
                        },
                    ]
                },
                {
                    'step': 3,
                    'title': 'QA测试',
                    'note': 'test note',
                    'action': 3,
                    'publish_host': [],
                },
                {
                    'step': 4,
                    'title': '部署master主机linesvr-web-mobile服务',
                    'note': 'test note',
                    'action': 1,
                    'publish_host': [
                        {
                            'application_name': 'linesvr-web-mobile',
                            'host_name': 'UGZB-TEST-A2-001',
                            'host_flag': 'master',
                        },
                    ]
                },
                {
                    'step': 5,
                    'title': '停slave主机linesvr-web-mobile服务',
                    'note': 'test note',
                    'action': 2,
                    'publish_host': [
                        {
                            'application_name': 'linesvr-web-mobile',
                            'host_name': 'UGZB-TEST-A2-002',
                            'host_flag': 'slave',
                        },
                    ]
                },
                {
                    'step': 6,
                    'title': 'QA测试',
                    'note': 'test note',
                    'action': 3,
                    'publish_host': [],
                },
                {
                    'step': 7,
                    'title': '部署剩下的全部',
                    'note': 'test note',
                    'action': 1,
                    'publish_host': [
                        {
                            'application_name': 'linesvr-mod-service',
                            'host_name': 'UGZB-TEST-M2-002',
                            'host_flag': 'slave',
                        },
                        {
                            'application_name': 'linesvr-web-mobile',
                            'host_name': 'UGZB-TEST-A2-002',
                            'host_flag': 'slave',
                        },
                    ]
                },
                {
                    'step': 8,
                    'title': 'QA测试',
                    'note': 'test note',
                    'action': 3,
                    'publish_host': [],
                },
            ]
        }
        response = self.session.post(self.url, json=payload)
        self.assertEqual(response.status_code, 200, response.status_code)
        result = response.json()['res']

        print(result)
        plan_id = result['id']

        db_res = self.db_session.query(PublishPattern).filter_by(publish_plan_id=plan_id).first()
        self.assertFalse(db_res is None)
        pattern_id = db_res.id

        db_res = self.db_session.query(PublishPatternHost).filter_by(publish_pattern_id=pattern_id).first()
        self.assertFalse(db_res is None)

