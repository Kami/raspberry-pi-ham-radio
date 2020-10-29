# -*- coding: utf-8 -*-
# Copyright 2020 Tomaz Muraus
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import unittest
import tempfile

import wx_server.configuration
from wx_server.app import create_app

from tests.unit.test_format_data import WU_PATH_DATA
from tests.unit.test_format_data import ECOWITT_FORM_DATA_DICT

__all__ = ["APIHandlersTestCase"]


class APIHandlersTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(APIHandlersTestCase, cls).setUpClass()

        # Use temporary directory for tests data path
        cls._app = create_app()
        cls.temp_dir = tempfile.mkdtemp()
        wx_server.configuration.CONFIG = {
            "main": {
                "data_dir": cls.temp_dir,
            },
            "secrets": {
                "home": "02812b7f3e16fa4eec98310587bc91090f1f45c79936da7827c7da060c2ea6ff",
            },
        }

    def test_handle_observation_wu_format_success(self):
        self.assertFalse(
            os.path.isfile(os.path.join(self.temp_dir, "home/2020/10/24/observation_1110.pb"))
        )

        client = self._app.test_client(self)
        resp = client.get("/v1/wx/observation/wu/" + WU_PATH_DATA)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, b"Observation saved")
        self.assertTrue(
            os.path.isfile(os.path.join(self.temp_dir, "home/2020/10/24/observation_1110.pb"))
        )

    def test_handle_observation_wu_format_failure(self):
        client = self._app.test_client(self)

        # 1. Not a valid method
        resp = client.post("/v1/wx/observation/wu/data")
        self.assertEqual(resp.status_code, 405)

        # 2. Not a valid station id / secret
        resp = client.get("/v1/wx/observation/wu/ID=invalid&PASSWORD=foobar")
        self.assertEqual(resp.status_code, 403)

        # 3. Not a valid station id / secret
        resp = client.get("/v1/wx/observation/wu/ID=invalid&PASSWORD=foobar")
        self.assertEqual(resp.status_code, 403)

        # 4. Invalid / missing payload data
        resp = client.get("/v1/wx/observation/wu/ID=home&PASSWORD=foobar")
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(b"Failed to parse incoming data" in resp.data)

    def test_handle_observation_ecowitt_format_success(self):
        client = self._app.test_client(self)

        self.assertFalse(
            os.path.isfile(os.path.join(self.temp_dir, "home/2020/10/18/observation_2023.pb"))
        )

        resp = client.post("/v1/wx/observation/ew/home/foobar", data=ECOWITT_FORM_DATA_DICT)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, b"Observation saved")

        self.assertTrue(
            os.path.isfile(os.path.join(self.temp_dir, "home/2020/10/18/observation_2023.pb"))
        )

    def test_handle_observation_ecowitt_format_failure(self):
        client = self._app.test_client(self)

        # 1. Not a valid method
        resp = client.get("/v1/wx/observation/ew/default/foo")
        self.assertEqual(resp.status_code, 405)

        # 2. Not a valid station id / secret
        resp = client.post("/v1/wx/observation/ew/default/foo")
        self.assertEqual(resp.status_code, 403)

        # 3. Not a valid station id / secret
        resp = client.post("/v1/wx/observation/ew/default/foobar")
        self.assertEqual(resp.status_code, 403)

        # 4. Invalid / missing payload data
        resp = client.post("/v1/wx/observation/ew/home/foobar")
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(b"Failed to parse incoming data" in resp.data)
