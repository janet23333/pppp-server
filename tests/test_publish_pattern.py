from tests.base import BaseTestCase


class PubilshPatternTestCase(BaseTestCase):
    def setUp(self):
        super(PubilshPatternTestCase, self).setUp()
        self.url = self.baseurl + '/publish_pattern'

    def test_get_format(self):
        response = self.session.get(self.url)
        self.assertEqual(response.status_code, 200, response.status_code)
        result = response.json()
        self.assertTrue('res' in result)
        self.assertTrue('total_count' in result)
        result = result['res']
        self.assertIsInstance(result, list, result)
        for pattern in result:
            self.assertTrue('publish_application_hosts' in pattern, pattern)
            apps = pattern['publish_application_hosts']
            self.assertIsInstance(apps, list, apps)
            for app in apps:
                self.assertTrue('publish_hosts' in app, app)
                hosts = app['publish_hosts']
                self.assertIsInstance(hosts, list, hosts)
                for host in hosts:
                    self.assertIsInstance(host, dict, host)
                    self.assertTrue('tasks' in host, host)
                    tasks = host['tasks']
                    self.assertIsInstance(tasks, list, tasks)

    def test_get_order_by(self):
        params = {'publish_plan_id': 128, 'order_by': 'step', 'desc': 1}
        response = self.session.get(self.url, params=params)
        self.assertEqual(response.status_code, 200, response.status_code)
        result = response.json()['res']
        self.assertGreater(result[0]['step'], result[1]['step'], result)

    def test_update_pattern(self):
        data = {'id': 108, 'status': 0}
        response = self.session.put(self.url, json=data)
        self.assertEqual(response.status_code, 200, response.status_code)
        result = response.json()['res']
        self.assertEqual(result['id'], data['id'], result)
        self.assertEqual(result['status'], data['status'], result)

        data = {'id': 108, 'status': 2}
        response = self.session.put(self.url, json=data)
        self.assertEqual(response.status_code, 200, response.status_code)
        result = response.json()['res']
        self.assertEqual(result['id'], data['id'], result)
        self.assertEqual(result['status'], data['status'], result)
