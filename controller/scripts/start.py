from flask_restful import Resource
from resources.resources import connectionstatus, device, healthcheck, hostconfig, journallogs, update, uuid, wififorget, wififorgetall
from resources.processes import curl, wifi
import resources.globals
import os, time, logging

#Disable Werkzeug logging to avoid flooding with access logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

print("Api-v1 - Starting API...")

#Wait for any saved connections to reconnect
time.sleep(20)

#Fetch container hostname and device hostname
containerhostname = os.popen('hostname').read().strip()
devicehostname = curl('get', '/v1/device/host-config?apikey=')

#Check container and device hostname match
if containerhostname != devicehostname.json()["network"]["hostname"]:
    print("Container hostname and device hostname do not match. Likely a hostname" + \
    "change has been performed. Balena Supervisor should detect this and rebuild " + \
    "the container shortly. Waiting 90 seconds before continuing anyway.")
    time.sleep(90)

#If connected to a wifi network then update device, otherwise launch wifi-connect
connected = os.popen('iwgetid -r').read().strip()
if connected:
    start = update().get()
    print("Api-v1 - API Started - Device connected to local wifi")
else:
    start = wifi().launch()
    print("Api-v1 - API Started - Controller launched")

#Configure API access points
if __name__ == '__main__':
    resources.globals.api.add_resource(connectionstatus, '/v1/connectionstatus')
    resources.globals.api.add_resource(device, '/v1/device')
    resources.globals.api.add_resource(healthcheck, '/')
    resources.globals.api.add_resource(hostconfig, '/v1/hostconfig/<hostname>') 
    resources.globals.api.add_resource(journallogs, '/v1/journallogs')
    resources.globals.api.add_resource(update, '/v1/update')
    resources.globals.api.add_resource(uuid, '/v1/uuid')
    resources.globals.api.add_resource(wififorget, '/v1/wififorget')
    resources.globals.api.add_resource(wififorgetall, '/v1/wififorgetall')

    resources.globals.app.run(port=9090,host='0.0.0.0')