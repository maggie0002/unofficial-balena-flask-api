from flask import Flask
from flask_restful import Resource, Api
from resources.resources import wificonnectionstatus, device, healthcheck, hostconfig, journallogs, update, uuid, wififorget, wififorgetall
from resources.processes import curl, wifi, wificonnect
import resources.globals
import atexit, logging, signal, subprocess, time

app = Flask(__name__)

api = Api(app)

print("Api-v1 - Starting API...")

#Wait for any saved connections to reconnect
time.sleep(20)

try:
    #Fetch container hostname and device hostname
    containerhostname = subprocess.run(["hostname"], capture_output=True, text=True).stdout.rstrip()
    devicehostname = curl(method = "get", path = "/v1/device/host-config?apikey=", supretries = 20)

    #Check container and device hostname match
    if containerhostname != devicehostname.json()["network"]["hostname"]:
        print("Api-v1 - Container hostname and device hostname do not match. Likely a hostname" + \
        "change has been performed. Balena Supervisor should detect this and rebuild " + \
        "the container shortly. Waiting 90 seconds before continuing anyway.")
        time.sleep(20)

except Exception as ex:
    print("Api-v1 - Failed to compare hostnames, starting anyway..." + str(ex))

#If connected to a wifi network then update device, otherwise launch wifi-connect
try:
    connected = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True).stdout.rstrip()
except Exception as ex:
    print("Api-v1 - Error executing iwgetid. Starting wifi-connect in order to allow debugging. " + str(ex))
    connected = None

if connected:
    update().get()
    print("Api-v1 - API Started - Device already connected to local wifi.")
else:
    try:
        wifimessage, wifistatuscode = wificonnect().start()
        if wifistatuscode == 200:
            print("Api-v1 - API Started - Wifi-Connect launched.")
        else:
            print(str(wifimessage), str(wifistatuscode))
    except Exception as ex: 
        print("Wifi-connect failed to launch. " + str(ex))

atexit.register(resources.processes.handle_exit, None, None)
signal.signal(signal.SIGTERM, resources.processes.handle_exit)
signal.signal(signal.SIGINT, resources.processes.handle_exit)

#Configure API access points
if __name__ == '__main__':
    api.add_resource(wificonnectionstatus, '/v1/wificonnectionstatus')
    api.add_resource(device, '/v1/device')
    api.add_resource(healthcheck, '/')
    api.add_resource(hostconfig, '/v1/hostconfig/<hostname>') 
    api.add_resource(journallogs, '/v1/journallogs')
    api.add_resource(update, '/v1/update')
    api.add_resource(uuid, '/v1/uuid')
    api.add_resource(wififorget, '/v1/wififorget')
    api.add_resource(wififorgetall, '/v1/wififorgetall')

    app.run(port=9090,host='0.0.0.0')