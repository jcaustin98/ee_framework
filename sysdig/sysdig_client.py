import os

from sdcclient import SdcClient


class SysdigClient(object):

    def __init__(self, token=""):
        if not token:
            token = os.getenv("SYSDIG_TOKEN")
        self._Token = token
        if not self._Token:
            raise ValueError((f"Invalid Sysdig configuration. "
                              f"Token not set (SYSDIG_TOKEN) or passes"))
        self._Severity = 7
        self._Client = SdcClient(self._Token)

    def write(self, **kwargs):
        msg = kwargs.get("description", "")
        if msg:
            self.post_alert({'name': msg,
                             'description': kwargs.get("data", ""),
                             'severity': kwargs.get('severity', self._Severity)})

    def post_alert(self, info):
        return self._Client.post_event(name=info['name'], description=info['description'],
                                       severity=info['severity'])

