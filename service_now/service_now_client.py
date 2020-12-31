import copy
import os
import requests
from typing import Any, Dict, Optional
import json
import urllib
import uuid


class ServiceNowClient(object):
    CreateInfo = {
        "assignedto": "delma@example.com",
        "system": "tef",
        "impact": "example impact description",
        "outageduration": "0 00:00:00",
        "priority": "moderate",
        "purpose": "Automated CR creation",
        "description": "Automated CR creation",
        "plannedstart": "now",
        "plannedend": "now",
        "deploymentready": "yes",
        "type": "standard",
        "backoutplan": "Backout Plan"
    }

    CloseInfo = { 
        "actualendtime": "now",
        "closecategory": "successful",
        "closenotes": "closed"
    }

    CreateTaskInfo = {
        "shortdescription": "Task Info",
        "system": "tef",
        "required": "not required", 
        "description": "Task Info",
        "data": "data text",
    }
    
    def __init__(self) -> None:
        # for testing, if the the env var SERVICE_NOW_TOKEN is NOT set, no api call will be made
        self.token = os.getenv("SERVICE_NOW_TOKEN")
        if self.token is None:
            raise Exception("CR failed: missing SERVICE_NOW_TOKEN")
        self.ServiceNowURL = os.getenv("Service_Now_URL", "")
        if self.ServiceNowURL is "":
            raise Exception("CR failed: missing Service_Now_URL")
        
    # Create a Change Request
    def create_change_request(self, region: str) -> str:
        if self.snow_api is not None:
            resp = self.snow_api("", "post", "create", self.CreateInfo)
            change_request = resp.json().get("result", {}).get("number")
        else:   # return default value for testing with no api
            change_request = "88"

        return change_request

    # Get the created Change Request
    def read_change_request(self, cr_id: str) -> str:
        resp = self.snow_api(cr_id, 'get', "read", {})

        return resp.text

    def snow_api(self, cr_id: str, method: str, action: str, payload: Dict) -> Any:
        if self.snow_api is None or self.ServiceNowURL is "":
            return

        func = getattr(requests, method)
        if func is None:
            msg = "CR {} failed: invalid http method {}".format(action, method)
            raise Exception(msg)

        cr_id_set = ""
        if "" != cr_id:
            cr_id_set = cr_id + '/'

        kargs = {
            "url": self.ServiceNowURL + cr_id_set + action,
            "headers": {
                "Accept": "application/xml",
            }
        }
        if "get" != method and "" != payload:
            kargs["json"] = payload
        
        resp = func(**kargs)
        if resp.status_code != 200:
            msg = "CR {} failed: code={} body={}".format(action, resp.status_code, resp.text)
            raise Exception(msg)

        return resp

    # Update the created Change Request
    def update_change_request(self, cr_id: str, data: Dict) -> None:
        if self.snow_api is not None:
            _ = self.snow_api(cr_id, "put", "update", data)

    # Close the Change Request
    def close_change_request(self, cr_id: str, data: Dict = None) -> int:
        if self.snow_api is None:
            return 502

        default = copy.deepcopy(self.CloseInfo)
        self._update_dict(data, default)

        resp = self.snow_api(cr_id, "put", "close", default)

        return resp.status_code

    def create_task(self, cr_id: str, data: Dict = None) -> int:
        if self.snow_api is None:
            return 502

        default = copy.deepcopy(self.CreateTaskInfo)
        self._update_dict(data, default)
        resp = self.snow_api(cr_id, "post", "task/create", default)

        return resp.status_code

    def _update_dict(self, source: Optional[Dict[Any, Any]], target: Optional[Dict[Any, Any]]) -> None:
        if source is None or target is None:
            return

        for k in target.keys():
            val = source.get(k, None)
            if val is not None:
                target[k] = val
