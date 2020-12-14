#!/usr/bin/env python
import json
import os
import unittest

import service_now_client

class ServiceNowClientTestCases(unittest.TestCase):
    def test_create_good(self):
        snow_cli = service_now_client.ServiceNowClient()
        self.assertNotEqual(snow_cli, None)

    def test_create_bad(self):
        cur = os.getenv("SERVICE_NOW_TOKEN")
        os.environ.pop("SERVICE_NOW_TOKEN")
        with self.assertRaises(Exception) as _:
            _ = service_now_client.ServiceNowClient()
        
        os.environ["SERVICE_NOW_TOKEN"] = cur 

    def test_create_cr(self):
        snow_cli = service_now_client.ServiceNowClient()
        self.assertNotEqual(snow_cli, None)
        cr_id = snow_cli.create_change_request("us-south")
        self.assertNotEqual(cr_id, "")
        snow_cli.close_change_request(cr_id)

    def test_close_cr_bad_id(self):
        snow_cli = service_now_client.ServiceNowClient()
        self.assertNotEqual(snow_cli, None)
        with self.assertRaises(Exception) as _:
            _ = snow_cli.close_change_request("kkkkaaasavvvv")

    def test_update_closenotes(self):
        snow_cli = service_now_client.ServiceNowClient()
        self.assertNotEqual(snow_cli, None)
        cr_id = snow_cli.create_change_request("us-south")
        self.assertNotEqual(cr_id, "")

        test_notes = "Phase 1, phase 2, Phase 3"
        snow_cli.close_change_request(cr_id, {"closenotes": test_notes})
        closed_cr = snow_cli.read_change_request(cr_id)
        self.assertEqual(test_notes, json.loads(closed_cr)["result"]["closenotes"])

    def test_create_task(self):
        snow_cli = service_now_client.ServiceNowClient()
        self.assertNotEqual(snow_cli, None)
        cr_id = snow_cli.create_change_request("us-south")
        self.assertNotEqual(cr_id, "")
        snow_cli.create_task(cr_id, {
            "shortdescription": "my test desc",
            "description": "my first task",
            "data": "WAHOO it worked"
        })

if __name__ == "__main__":
    unittest.main()
