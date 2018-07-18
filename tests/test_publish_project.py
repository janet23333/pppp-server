from tests.base import BaseTestCase
from orm.models import PublishProject
from orm.db import session_scope


class PublishProjectTestCase(BaseTestCase):
    def setUp(self):
        super(PublishProjectTestCase, self).setUp()
        self.url = self.baseurl + '/publish_project'

    def test_create_project(self):
        payload = {"name": "test_project"}
        response = self.session.post(self.url, json=payload)
        self.assertEqual(response.status_code, 200)
        project_id = response.json()['res']['id']
        with session_scope() as ss:
            r = ss.query(PublishProject).filter_by(id=project_id).one_or_none()
            self.assertNotEqual(r, None)

    def test_missing_create_argument(self):
        payload = {}
        response = self.session.post(self.url, json=payload)
        self.assertEqual(response.status_code, 400)

    def test_get_project_filter_by_name(self):
        payload = {
            "name": "test_project"
        }

        response = self.session.get(self.url, params=payload)
        self.assertEqual(response.status_code, 200)

        res = response.json()['res']
        for project in res:
            self.assertEqual(project["name"], payload["name"], project)

    def test_get_project_filter_by_id(self):
        payload = {
            "id": 1
        }

        response = self.session.get(self.url, params=payload)
        self.assertEqual(response.status_code, 200)

        res = response.json()['res']
        for project in res:
            self.assertEqual(project["id"], payload["id"], project)

    def test_get_project_order_by_id(self):
        payload = {
            "order_by": "id",
            "desc": 1
        }

        response = self.session.get(self.url, params=payload)
        self.assertEqual(response.status_code, 200)

        res = response.json()['res']
        id_list = [p['id'] for p in res]
        for i in range(-1, len(id_list)):
            if i == 0:
                continue

            self.assertGreater(id_list[i-1], id_list[i])

    def test_update_project_status(self):
        payload = {
            "id": 1,
            "status": 0,
        }

        response = self.session.put(self.url, json=payload)
        self.assertEqual(response.status_code, 200)
        res = response.json()['res']
        self.assertEqual(res['status'], payload['status'], res)

        payload = {
            "id": 1,
            "status": 1,
        }

        response = self.session.put(self.url, json=payload)
        self.assertEqual(response.status_code, 200)
        res = response.json()['res']
        self.assertEqual(res['status'], payload['status'], res)

    def test_delete_project(self):
        payload = {
            "id": 1
        }

        resp = self.session.delete(self.url, json=payload)
        self.assertEqual(resp.status_code, 200, resp.json())
        with session_scope() as ss:
            db_res = ss.query(PublishProject).filter_by(id=payload['id']).one()
            self.assertEqual(db_res.is_delete, 1, db_res)

    def test_get_project_filter_by_user_id(self):
        payload = {
            "create_user_id": 5,
        }
        resp = self.session.get(self.url, params=payload)
        self.assertEqual(resp.status_code, 200, resp.json())
        res = resp.json()['res']
        for p in res:
            self.assertEqual(p['create_user']['id'], payload['create_user_id'], p)
