from tests.base import BaseTestCase


class PublishPatternHostTestCase(BaseTestCase):
    def setUp(self):
        super(PublishPatternHostTestCase, self).setUp()
        self.url = self.baseurl + '/pattern_host'

    def test_modify_pattern_host_status(self):
        payload = {
            'id': 1868,
            'status': 3,
        }
        resp = self.session.put(self.url, json=payload)
        self.assertEqual(resp.status_code, 200, resp.json())

        res = resp.json()['res']
        self.assertEqual(res['status'], payload['status'], res)
        for t in res['publish_pattern_tasks']:
            self.assertEqual(t['status'], payload['status'], t)

    def test_modify_pattern_host_status_filter_by_pattern_id_and_host_id(self):
        payload = {
            'publish_pattern_id': 1668,
            'publish_host_id': 1920,
            'status': 3,
        }
        resp = self.session.put(self.url, json=payload)
        self.assertEqual(resp.status_code, 200, resp.json())

        res = resp.json()['res']
        self.assertEqual(res['status'], payload['status'], res)
        for t in res['publish_pattern_tasks']:
            self.assertEqual(t['status'], payload['status'], t)