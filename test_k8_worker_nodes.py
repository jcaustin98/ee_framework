import datetime
import os
import unittest

from events import events_name_space
from k8_worker_nodes import UpdateK8WorkerNodes
from service_now import service_now_client
from slack import slack_client
from sysdig import sysdig_client

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
        cur_color = kwargs.get("color", None)
        kwargs["color"] = "warning"
        super(SummarySlackClient, self).post_event_message(**kwargs)
        if cur_color is None:
            del kwargs["color"]
        else:
            kwargs["color"] = cur_color
        

class UpdateSNowClientTestCase(unittest.TestCase):
    def test_create_task(self):
        try:
            snow_cli = UpdateK8WorkerNodes()
        except:
            pass  # No service now token defined
        task_names = snow_cli.get_task_names()
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

        # sysdig client for alerting to sysdig monitoring system
        # register all events to explain k8 alerts from update
        sysdig_cli = sysdig_client.SysdigClient()
        events.register(task_names, sysdig_cli.write)

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

        packet["data"] = ('Evidence for removing systems from traffic, in this case using DNS\n',
                          'commands to remove\n and commands to show it\'s removed')
        events.emit("update.dns.disable", **packet)

        packet["data"] = ('Evidence for updating worker nodes,\n like show start version and ',
                          'end version for all nodes or each node as it gets done')
        packet["NODE"] = "Add a special template variable, in that is casee the node being updated"
        events.emit("update.worker.start", **packet)

        packet["data"] = 'Evidence for system and/or software testing completed after the update has been completed'
        events.emit("update.test", **packet)

        packet["data"] = 'Evidence for putting system(s) back into traffic rotation'
        events.emit("update.dns.enable", **packet)

        snow_cli.close_change_request(cr_id)

        packet["data"] = "changed request closed"
        events.emit("update.cr.close", **packet)
    
        packet["data"] = "Update done at %s. Congratulations" % datetime.datetime.utcnow().isoformat()
        events.emit("update.done", **packet)

