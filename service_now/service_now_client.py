import copy
import os
import requests
import json
import urllib
import uuid


class ServiceNowClient(object):
    # ServiceNowURL used to talk to the prod ServiceNow
    #'https://watson.service-now.com/api/ibmwc/v1/change/'
    # ServiceNowTestURL used to talk to the test servicenow instance
    # "https://watsontest.service-now.com/api/ibmwc/change/"
    ServiceNowURL = "https://watsontest.service-now.com/api/ibmwc/change/"

    CreateInfo = {
        "assignedto": "mike.little@us.ibm.com",
        "system": "kms",
        "impact": "example impact description",
        "outageduration": "0 00:00:00",
        "priority": "moderate",
        "environment": "ibm:ys1:",
        "purpose": "Key Protect Automated CR creation",
        "description": "Key Protect Automated CR creation",
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
        "shortdescription": "Key Protect task",
        "system": "kms",
        "required": "not required", 
        "description": "Key Protect task",
        "data": "data text",
        "targetscore": "100",
        "targettype": "greater than",
        "actualscore": "100"
    }
    

    #def __init__(self):
        #  commented out for testing with no service now connection
        #self.token = os.getenv("SERVICE_NOW_TOKEN")
        #if self.token is None:
        #    raise Exception("CR failed: missing SERVICE_NOW_TOKEN")
        

    # Create a Change Request
    def create_change_request(self, region):
        self.CreateInfo["environment"] =  "ibm:ys1:{}".format(region)
        #  commented out for testing with no service now connection
        #resp = self.snow_api("", "post", "create", self.CreateInfo)
        #change_request = resp.json().get("result", {}).get("number")
        print(f"POST - CREATE - {self.CreateInfo}")
        change_request = '88'

        return change_request

    # Get the created Change Request
    def read_change_request(self, cr_id):
        resp = self.snow_api(cr_id, 'get', "read", "")

        return resp.text

    def snow_api(self, cr_id, method, action, payload):
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
    def update_change_request(self, cr_id, data):
        #  commented out for testing with no service now connection
        #_ = self.snow_api(cr_id, "put", "update", data)
        print(f"UPDATE - PUT - {cr_id} - {data}")
        
    # Close the Change Request
    def close_change_request(self, cr_id, data = None):
        default = copy.deepcopy(self.CloseInfo)
        self._update_dict(data, default)

        #  commented out for testing with no service now connection
        #resp = self.snow_api(cr_id, "put", action='close', payload = default)
        print(f"CLOSE - PUT - {cr_id} - {default}")
        resp = f"CLOSE - PUT - {cr_id} - {default}"
        return resp

    def create_task(self, cr_id, data=None):
        default = copy.deepcopy(self.CreateTaskInfo)
        self._update_dict(data, default)
        ret = self.snow_api(cr_id, "post", "task/create", default)
        # self.slack.write("", attachments=[
        #     {"text": "Created Task \n``` {} ```".format(default), 
        #     "color": "good"
        #     }])
        return ret

    def _update_dict(self, source, target):
        if source is None:
            return
        for k in target.keys():
            val = source.get(k, None)
            if val is not None:
                target[k] = val
