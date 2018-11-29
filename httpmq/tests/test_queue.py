import json
import os
import sys

import tornado
from tornado.testing import AsyncHTTPTestCase

import server

current_path = os.path.dirname(os.getcwd())
sys.path.insert(0, current_path)


class BaseTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return server.make_app("test")

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.current()


class QueueTestCase(BaseTestCase):
    test_name = "test_case"
    test_data = 1
    test_param = {
            "name": test_name,
            "data": test_data
        }

    def test_queue_get(self):
        self.test_queue_put()
        url = f"/queue/?name={self.test_name}"
        response = self.fetch(url)
        self.assertIn(b"HTTPMQ_SUCCEED", response.body)

    def test_queue_put(self):
        url = "/queue/"
        response = self.fetch(url, method="PUT",
                              body=json.dumps(self.test_param))
        self.assertIn(b"HTTPMQ_PUT_OK", response.body)

    def test_reset(self):
        url = f"/reset/?name={self.test_name}"
        response = self.fetch(url)
        self.assertIn(b"HTTPMQ_RESET_OK", response.body)

    def test_status(self):
        self.test_queue_put()
        url = f"/status/?name={self.test_name}"
        response = self.fetch(url)
        self.assertIn(b"HTTPMQ_SUCCEED", response.body)

    def test_view(self):
        url = f"/view/?name={self.test_name}&position=0"
        response = self.fetch(url)
        self.assertIn(b"HTTPMQ_SUCCEED", response.body)
        self.test_reset()  # tearDownClass
