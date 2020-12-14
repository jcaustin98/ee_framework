import datetime
import os
import unittest

from events import events_name_space
from service_now import service_now_client
from slack import slack_client

# wrapper for summary slack client
class SummarySlackClient(slack_client.SlackClient):

    def __init__(self, token="", defaults=None):
        defaults = {
            "channel": os.getenv("SLACK_SUMMARY_HOOK_CHANNEL"),
            "hook": os.getenv("SLACK_SUMMARY_HOOK_URL"),
        }
        super(SummarySlackClient, self).__init__(token=token, defaults=defaults)

    # make yellow message bar for summary
    def post_event_message(self, **kwargs):
        #import pdb;pdb.set_trace()
        cur_color = kwargs.get("color", None)
        kwargs["color"] = "warning"
        super(SummarySlackClient, self).post_event_message(**kwargs)
        if cur_color is None:
            del kwargs["color"]
        else:
            kwargs["color"] = cur_color
        

class UpdateSNowClientTestCase(unittest.TestCase):

    # def test_create_cr(self):
    #     snow_cli = UpdateSNowClient()
    #     self.assertNotEqual(snow_cli, None)
    #     cr_id = snow_cli.create_change_request("us-south")
    #     self.assertNotEqual(cr_id, "")
                
    #     #self.assertEqual(cr["result"]["impact"], "No expected impact or downtime to us-south for this deployment")
    #     snow_cli.close_change_request(cr_id)

    def test_create_task(self):
        snow_cli = UpdateSNowClient()
        events = events_name_space.EventNameSpace()
        # order of events IS important. The returns from the hook functions will
        # pipelined by adding them to the kwargs id a dict is returned
        ##
        # In this example, the UpdateSNowClient adds the description of the
        # current task and the slack clients post them 
        snow_cli.register_events(events)

        # slack client for full details - deploy - registers for all events
        full_chan = slack_client.SlackClient() 
        snow_cli.register_events(events, full_chan.post_event_message)

        # slack client for summary messages - on-call - only registers
        # for region/zone start and end and DNS changes, DNS uses namespace wild card
        summary_chan = SummarySlackClient()
        events.register(["update.start", "update.done", "update.dns.*"], summary_chan.post_event_message)

        region = "us-south"
        zone = "dc10"
        self.assertNotEqual(snow_cli, None)
        
        cr_id = snow_cli.create_change_request(region)

        # Set some variables in the data packet for templates
        # By convention, all capital identifiers are interpreted as template variables
        packet = {"CR_ID": cr_id, "REGION": region, "ZONE": zone}

        # Set "data" with the event specific message
        packet["data"] = "changed request created"
        events.emit("update.cr.create", **packet)
        self.assertNotEqual(cr_id, "")
        
        packet["data"] = "Update started at %s" % datetime.datetime.utcnow().isoformat()
        events.emit("update.start", **packet)

        packet["data"] = '''INFO:__main__:Removing dal10 from load balancer
INFO:redstone.auth:httplib POST /oidc/token
'''
        events.emit("update.dns.disable", **packet)

        packet["data"] = '''INFO:__main__:ID                                                   VERSION                                       STATUS
INFO:__main__:kube-dal10-crb1c781bd91bc45208d015398edf0124c-w1     1.10.12_1546                                  Ready               
'''
        packet["NODE"] = "kube-dal10-crb1c781bd91bc45208d015398edf0124c-w1"
        events.emit("update.worker.start", **packet)

        packet["data"] = '''Creating instance
Created instance(name=mrodden_test_deleteme-us-east-5e84d39fe70143f3a859ee4d0f3a4f46, instance_id=d34225ff-2224-482e-9f12-77c10f6c6680, crn=crn:v1:bluemix:public:kms:us-east:a/7609edf6db359a81a1dde8f44b1a8278:d34225ff-2224-482e-9f12-77c10f6c6680::)
Deleted instance
'''
        events.emit("update.test", **packet)

        packet["data"] = '''INFO:__main__:Tests passes. Putting back in load balancer (Dyn)
INFO:fixatron.deploy:Setting CIS record wdc07 to state enabled=True
'''
        events.emit("update.dns.enable", **packet)

        snow_cli.close_change_request(cr_id)

        packet["data"] = "changed request closed"
        events.emit("update.cr.close", **packet)
    
        packet["data"] = "Update done at %s. Congratulations" % datetime.datetime.utcnow().isoformat()
        events.emit("update.done", **packet)
        


class UpdateSNowClient(service_now_client.ServiceNowClient):
    CreateInfo = {
            "assignedto": "adriano.santos@ibm.com",
            "system": "kms",
            "impact": "No expected impact or downtime to REGION for this deployment",
            "outageduration": "0 00:00:00",
            "priority": "moderate",
            "environment": "ibm:ys1:REGION", # need to check for value
            "purpose": "Update IBM Kubernetes Service worker nodes to VERSION",
            "description": '''
Work and compliance steps:
1. Start the task on the first selected DC in region
    Record process start time for the first selected DC in the region
2. Disable first selected DC in the region in DYN DNS.
    Record information for this task
3. Update the kubernetes nodes in the first selected DC in the region.
    Record all nodes from and to versions
    Record all nodes up and ready on the new version
4. Run end to end testing of service functionality in updated DC
    Record all test results
5. Enable the first selected DC in the region in DYN DNS.
    Record information for this task
6. Update compleated for first selected DC in the region
    Record  completion time for the DC and region

Repeat all tasks for the second DC

If the tests fail, changes stop

6. Update worker nodes in the region's tooling cluster.
_________ what is needed for compliance ????
''',
            "plannedstart": "now + 24 houts", # calculate
            "plannedend": "now + 24 hours",# calculate
            "deploymentready": "yes",
            "type": "standard",
            "backoutplan": "Updates will be stopped and fixes will be fast tracked to that DC. Then a deploy of those fixes will happen and the update will continue"
        }
    TaskBase = {
        "shortdescription": "",
        "system": "kms",
        "required": "required", 
        "description": "", 
        "data": "DATA",
        "targetscore": "100",
        "targettype": "greater than",
        "actualscore": "100"
    }
    TasksInfo = {
        "update.start": {
            "shortdescription": "Start k8 update in REGION ZONE at TIME",
            "description": "Start k8 update in REGION ZONE at TIME",
        },
        "update.cr.create": {
            "shortdescription": "Created CR CR_ID for k8 update in REGION ZONE",
            "description": "Created CR CR_ID for k8 update in REGION ZONE",
        },
        "update.cr.close": {
            "shortdescription": "Close CR CR_ID for k8 update in REGION",
            "description": "Close CR CR_ID for k8 update in REGION",
        },
        "update.dns.disable": {
            "shortdescription": "Disable ZONE in REGION in DYN DNS.",
            "description": "Disable ZONE in REGION in DYN DNS.",
        },
        "update.worker.start": {
            "shortdescription": "Update NODE in Zone REGION.",
            "description": "Update NODE in Zone REGION.",
        },
        "update.worker.done": {
            "shortdescription": "Update done for NODE in Zone REGION.",
            "description": "Update done for NODE in Zone REGION.",
        },
        "update.test":{
            "shortdescription": "Run end to end testing of KP services functionality in updated ZONE REGION.",
            "description": "Run end to end testing of KP services functionality in updated ZONE REGION.",
        },
        "update.dns.enable": {
            "shortdescription": "Enable the ZONE in REGION in DYN DNS.",
            "description": "Enable the ZONE in REGION in DYN DNS.",
        },
        "update.done": {
            "shortdescription": "Update compleated for ZONE in REGION.",
            "description": "Update compleated for ZONE in REGION.",
        },
    }

    def register_events(self, event_obj, cb=None):
        call_back = cb
        if cb is None:
            call_back = self.create_task
        for ens in self.TasksInfo.keys():
            event_obj.register(ens, call_back)

    def template_string(self, body, **kwargs):
        tmp = {"body": body}
        self.template_data(tmp, **kwargs)
        return tmp["body"]

    def template_data(self, source_data, **kwargs):
        for k in source_data.keys():
            for kw, kv in kwargs.items():
                source_data[k] = source_data[k].replace(kw, kv)

    def _format_time(self, dt):
        return "%s" % dt.isoformat().replace("T", " ").split('.')[0]

    def task_description(self, name, **kwargs):
        cur_task = self.TasksInfo.get(name)
        return self.template_string(cur_task["description"], **kwargs)

    def create_change_request(self, region):
        start = datetime.datetime.utcnow()
        self.CreateInfo["plannedstart"] = self._format_time(start)
        end = start + datetime.timedelta(days=5)
        self.CreateInfo["plannedend"] = self._format_time(end)
        return super(UpdateSNowClient, self).create_change_request(region)

    def create_task(self, **kwargs):
        cur_task = self.TasksInfo.get(kwargs.get("event_name"))
        kwargs["TIME"] = self._format_time(datetime.datetime.utcnow())
 
        if cur_task is None:
            return
        full_task = {**self.TaskBase, **cur_task}
        full_task["data"] = kwargs.get("data", "")
        
        self.template_data(full_task, **kwargs)

        ret = {"description": full_task["description"]}
        #  commented out for testing with no service now connection
        #ret["result"] = self.snow_api(kwargs["CR_ID"], "post", "task/create", full_task)
        print(f"task/create - POST - {kwargs['CR_ID']} - {full_task}")
        ret["result"] = 200

        # self.slack.write("", attachments=[
        #     {"text": "``` {} ```".format(full_task["shortdescription"]), 
        #     "color": "good"
        #     }])
        return ret
