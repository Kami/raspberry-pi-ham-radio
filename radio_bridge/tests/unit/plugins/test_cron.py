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
import datetime

import mock

from radio_bridge.plugins.cron import CronSayPlugin
from radio_bridge.configuration import get_plugin_config
from radio_bridge.configuration import _load_and_parse_config

from tests.unit.plugins.base import BasePluginTestCase
from tests.unit.plugins.base import MockBasePlugin

__all__ = ["CronSayPluginTestCase"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../fixtures/configs/config3.ini"))


class CronSayPluginForTest(CronSayPlugin, MockBasePlugin):
    pass


class CronSayPluginTestCase(BasePluginTestCase):
    def test_parse_and_validate_config_success(self):
        _load_and_parse_config(config_path=CONFIG_PATH)

        plugin_config = get_plugin_config(CronSayPlugin.ID)
        self.assertEqual(len(plugin_config), 5)

        plugin = CronSayPlugin()

        job_id_to_config_map = plugin._parse_and_validate_config(config=plugin_config)
        self.assertEqual(len(job_id_to_config_map), 5)

        # Text say job
        job_id = "say_current_time_every_120_seconds"
        job = job_id_to_config_map[job_id]

        self.assertEqual(job.job_id, job_id)
        self.assertEqual(job.type, "text")
        self.assertEqual(job.value, "Current time is {time_utc} UTC.")
        self.assertEqual(job.trigger_instance.interval, datetime.timedelta(seconds=120))

        # Text to morse say job
        job_id = "say_text_as_morse_every_200_seconds"
        job = job_id_to_config_map[job_id]

        self.assertEqual(job.job_id, job_id)
        self.assertEqual(job.type, "text_to_morse")
        self.assertEqual(job.value, "sos")
        self.assertEqual(job.trigger_instance.interval, datetime.timedelta(seconds=200))

        # Morse say job
        job_id = "say_morse_code_every_400_seconds"
        job = job_id_to_config_map[job_id]

        self.assertEqual(job.job_id, job_id)
        self.assertEqual(job.type, "morse")
        self.assertEqual(job.value, "... --- ...")
        self.assertEqual(job.trigger_instance.interval, datetime.timedelta(seconds=400))

        # Play file job (interval trigger)
        job_id = "play_callsign_every_500_seconds"
        job = job_id_to_config_map[job_id]

        self.assertEqual(job.job_id, job_id)
        self.assertEqual(job.type, "file")
        self.assertEqual(job.value, "tests/fixtures/audio/plugin_current_time.wav")
        self.assertEqual(job.trigger_instance.interval, datetime.timedelta(seconds=500))

        # Play file job (cron trigger)
        job_id = "play_callsign_every_5_minutes"
        job = job_id_to_config_map[job_id]

        self.assertEqual(job.job_id, job_id)
        self.assertEqual(job.type, "file")
        self.assertEqual(job.value, "tests/fixtures/audio/plugin_current_time.wav")
        self.assertEqual(
            str(job.trigger_instance),
            "cron[month='*', day='*', day_of_week='*', hour='*', minute='*/5']",
        )

    def test_parse_and_validate_config_failure(self):
        plugin = CronSayPlugin()

        # 1. Requested interval is greater than minimum run interval
        plugin_config = {"say_test": "interval;seconds=10;text;Test."}

        expected_msg = (
            "Requested interval for job say_test is 10 seconds, but minimum allowed "
            "value is 120 seconds"
        )
        self.assertRaisesRegex(
            ValueError, expected_msg, plugin._parse_and_validate_config, config=plugin_config
        )

        # 2. Referenced file doesn't exist
        plugin_config = {"say_audio_file": "interval;seconds=300;file;doesntexist.mp3"}

        expected_msg = "File doesntexist.mp3 doesn't exist"
        self.assertRaisesRegex(
            ValueError, expected_msg, plugin._parse_and_validate_config, config=plugin_config
        )

    @mock.patch("radio_bridge.plugins.cron.datetime")
    def test_get_text_format_context(self, mock_datetime):
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2020, 10, 26, 19, 57)
        mock_datetime.datetime.now.return_value = datetime.datetime(2020, 10, 26, 20, 57)

        plugin = CronSayPlugin()
        context = plugin._get_text_format_context()

        expected_context = {
            "callsign": "TEST",
            "day_of_week": "Monday",
            "date": "2020-10-26",
            "time_utc": "19:57",
            "time_local": "20:57",
            "weather_data": {},
        }
        self.assertEqual(context, expected_context)

    @mock.patch("radio_bridge.plugins.cron.datetime")
    def test_run_success_text_job(self, mock_datetime):
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2020, 10, 26, 14, 16)

        _load_and_parse_config(config_path=CONFIG_PATH)
        plugin_config = get_plugin_config(CronSayPlugin.ID)

        plugin = CronSayPluginForTest()
        plugin.initialize(config=plugin_config)

        self.assertEqual(len(plugin.mock_said_text), 0)

        job_id = "say_current_time_every_120_seconds"
        plugin.run(job_id=job_id)

        expected_text = "Current time is 14:16 UTC."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    @mock.patch("morse.Morse")
    def test_run_success_text_to_morse_job(self, mock_morse):
        mock_morse_instance = mock.Mock()
        mock_morse.return_value = mock_morse_instance

        _load_and_parse_config(config_path=CONFIG_PATH)
        plugin_config = get_plugin_config(CronSayPlugin.ID)

        plugin = CronSayPluginForTest()
        plugin.initialize(config=plugin_config)

        self.assertEqual(mock_morse_instance.transmit.call_count, 0)

        job_id = "say_text_as_morse_every_200_seconds"
        plugin.run(job_id=job_id)

        mock_morse.assert_called_with(words="sos")
        self.assertEqual(mock_morse_instance.transmit.call_count, 1)

    @mock.patch("morse.Morse")
    def test_run_success_morse_job(self, mock_morse):
        mock_morse_instance = mock.Mock()
        mock_morse.return_value = mock_morse_instance

        _load_and_parse_config(config_path=CONFIG_PATH)
        plugin_config = get_plugin_config(CronSayPlugin.ID)

        plugin = CronSayPluginForTest()
        plugin.initialize(config=plugin_config)

        self.assertEqual(mock_morse_instance.transmit.call_count, 0)

        job_id = "say_morse_code_every_400_seconds"
        plugin.run(job_id=job_id)

        mock_morse.assert_called_with(morse="... --- ...")
        self.assertEqual(mock_morse_instance.transmit.call_count, 1)

    def test_run_success_file_job(self):
        _load_and_parse_config(config_path=CONFIG_PATH)
        plugin_config = get_plugin_config(CronSayPlugin.ID)

        plugin = CronSayPluginForTest()
        plugin.initialize(config=plugin_config)
        plugin._audio_player = mock.Mock()

        self.assertEqual(plugin._audio_player.play_file.call_count, 0)

        job_id = "play_callsign_every_5_minutes"
        plugin.run(job_id=job_id)

        plugin._audio_player.play_file.assert_called_with(
            file_path="tests/fixtures/audio/plugin_current_time.wav", delete_after_play=False
        )
        self.assertEqual(plugin._audio_player.play_file.call_count, 1)
