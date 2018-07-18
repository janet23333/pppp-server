from tests.base import BaseTestCase
from orm.models import PublishProject
from orm.db import session_scope


class RollbackTestCase(BaseTestCase):
    def setUp(self):
        super(RollbackTestCase, self).setUp()
        self.url = self.baseurl + '/rollback'

    def test_run_rollback(self):
        payload = {"publish_plan_id": 406}
        response = self.session.post(self.url, json=payload)
        self.assertEqual(response.status_code, 200)
        # project_id = response.json()['res']['id']
        # with session_scope() as ss:
        #     r = ss.query(PublishProject).filter_by(id=project_id).one_or_none()
        #     self.assertNotEqual(r, None)
