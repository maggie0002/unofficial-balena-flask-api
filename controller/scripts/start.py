from flask import Flask
from flask_restful import Resource, Api
from resources.resources import connectionstatus, device, healthcheck, hostconfig, journallogs, update, uuid, wififorget, wififorgetall
from resources.processes import curl, wifi
import resources.globals
import time, logging, subprocess

app = Flask(__name__)

api = Api(app)

print("Api-v1 - Starting API...")

#Wait for any saved connections to reconnect
time.sleep(20)

try:
    #Fetch container hostname and device hostname
    containerhostname = subprocess.run(["hostname"], capture_output=True, text=True).stdout.rstrip()
    devicehostname = curl(method = "get", path = "/v1/device/host-config?apikey=", timeout = 5, supretries = 10)

    #Check container and device hostname match
    if containerhostname != devicehostname.json()["network"]["hostname"]:
        print("Api-v1 - Container hostname and device hostname do not match. Likely a hostname" + \
        "change has been performed. Balena Supervisor should detect this and rebuild " + \
        "the container shortly. Waiting 90 seconds before continuing anyway.")
        time.sleep(90)

except:
    print("Api-v1 - Failed to compare hostnames, starting anyway...")

#If connected to a wifi network then update device, otherwise launch wifi-connect
connected = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True).stdout.rstrip()
if connected:
    update().get()
    print("Api-v1 - API Started - Device connected to local wifi")
else:
    wifimessage, wifistatuscode = wifi().launch()

    if wifistatuscode != 200:
        print('Api-v1 - start.py unable to start wifi - ' + str(wifimessage))
    else:
        print("Api-v1 - API Started - Controller launched")

#Configure API access points
if __name__ == '__main__':
    api.add_resource(connectionstatus, '/v1/connectionstatus')
    api.add_resource(device, '/v1/device')
    api.add_resource(healthcheck, '/')
    api.add_resource(hostconfig, '/v1/hostconfig/<hostname>') 
    api.add_resource(journallogs, '/v1/journallogs')
    api.add_resource(update, '/v1/update')
    api.add_resource(uuid, '/v1/uuid')
    api.add_resource(wififorget, '/v1/wififorget')
    api.add_resource(wififorgetall, '/v1/wififorgetall')

    app.run(port=9090,host='0.0.0.0')