from sdcclient import SdcClient

# 30 day dev
# d416132e-2285-4d85-b9cc-84d02be3cef1
# https://app.sysdigcloud.com


sdclient = SdcClient('d416132e-2285-4d85-b9cc-84d02be3cef1')
#ok, res = client.PostAlert(alert_info)
test = {
    'name': 'test 1',
    'description': 'This is a test of the national broadcast system',
    'severity': 5,
    'scope': '',
    'tags': '{"action":"UpgradeWorkerNodes"}'
}

def PostAlert(client, info):
    return client.post_event(name=info['name'], description=info['description'],
                             severity=info['severity'])

ok, resp = PostAlert(sdclient, test)
print(ok,'\n', resp)