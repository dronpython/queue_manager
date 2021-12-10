import unittest
import uuid
from connectors.old_api import old_api_request
from connectors.DBconnector import db, query_dict


class TestConnection(unittest.TestCase):

    uid = str(uuid.uuid4())
    endpoint = '/test/endpoint'
    domain = 'sigma'
    username = 'testuser'
    status = 'done'
    new_status = 'working'

    def test_insertation(self):

        db.insert_data('queue_main', self.uid, self.endpoint, self.domain, self.username, self.status)
        data = db.universal_select(f"SELECT * FROM queue_main WHERE request_id = '{self.uid}'")

        self.assertTrue(data[0], 'No data to select')
        self.assertEqual(data[0].endpoint, self.endpoint, 'ENDPOINT not equals')
        self.assertEqual(data[0].request_id, self.uid, 'UUID not equals')
        self.assertEqual(data[0].domain, self.domain, 'DOMAIN not equals')
        self.assertEqual(data[0].username, self.username, 'USERNAME not equals')
        self.assertEqual(data[0].status, self.status, 'STATUS not equals')

    def test_updating(self):
        query = query_dict["update_main_then_finished"].format(request_id=self.uid, status=self.new_status)
        db.universal_update(query)
        data = db.universal_select(f"SELECT * FROM queue_main WHERE request_id = '{self.__class__.uid}'")
        self.assertTrue(data[0], 'No data to select')
        self.assertEqual(data[0].status, self.new_status, 'STATUS not equals')

    def test_api_connector(self):
        endpoint = '/api/v3/nexus/info'
        headers = {}
        req_type = 'POST'
        req_body = {}
        response = old_api_request(endpoint, req_type, req_body, headers)
        self.assertEqual(response.status_code, 401, 'Status codes not equal')


if __name__ == '__main__':
    unittest.main()
