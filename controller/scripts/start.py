from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
from resources.exitcodes import exitgen
import os, requests, NetworkManager, time, subprocess, logging

#Required variables to be set by user#
deafultssid = 'choose-a-default-ssid-here'
defaulthostname = 'put-device-hostname-you-built-your-device-with-here'
#####################################

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

api = Api(app)

BALENA_SUPERVISOR_API_KEY = os.environ['BALENA_SUPERVISOR_API_KEY']
BALENA_SUPERVISOR_ADDRESS = os.environ['BALENA_SUPERVISOR_ADDRESS']

print("Api-v1 - Starting API...")

time.sleep(15)

def curl(request, balenaurl, data):

    if request == 'post':
        response = requests.post(
            f'{BALENA_SUPERVISOR_ADDRESS}{balenaurl}{BALENA_SUPERVISOR_API_KEY}',
            json=[data],
            headers={"Content-Type": "application/json"},
        )

    elif request == 'patch':

        response = requests.patch(
            f'{BALENA_SUPERVISOR_ADDRESS}{balenaurl}{BALENA_SUPERVISOR_API_KEY}',
            data=data,
            headers={"Content-Type": "application/json"},
        )

    elif request == 'get':

        response = requests.get(
            f'{BALENA_SUPERVISOR_ADDRESS}{balenaurl}{BALENA_SUPERVISOR_API_KEY}',
            headers={"Content-Type": "application/json"},
        )

    return response
    
def launchwifi():
    currenthostname = curl('get', '/v1/device/host-config?apikey=', '')
    if currenthostname.json()["network"]["hostname"]:
        if currenthostname.json()["network"]["hostname"] == defaulthostname:
            cmd = f'/app/common/wifi-connect/wifi-connect -s {deafultssid} -o 8080 --ui-directory custom-ui'.split()
        else:
            cmd = f'/app/common/wifi-connect/wifi-connect -s {currenthostname.json()["network"]["hostname"]} -o 8080 --ui-directory custom-ui'.split()

        p = subprocess.Popen(cmd, stdout = subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE)

        with app.app_context():
            if p.returncode == None:
                exitstatus = make_response("Api-v1 - Launchwifi: Wifi-Connect launched.", 200)
            else:
                exitstatus = make_response("Api-v1 - Launchwifi: Wifi-Connect launch failure.", 500)

        print(exitstatus.data.decode("utf-8"), exitstatus.status_code)

    else:
        print("Api-v1 - Launchwifi: Hostname is blank. This is a fatal error.")
        exitstatus = make_response("Hostname is blank. This is a fatal error.", 500)

    return exitstatus

class connectionstatus(Resource):
    def get(self):

        run = os.popen('iwgetid -r').read().strip()

        if run:
            status = 200
        else:
            curlwifi = os.system('ping -c 1 -w 1 -I wlan0 192.168.42.1 >/dev/null 2>&1')

            if curlwifi == 0:
                status = 206
            else:
                status = 500

        exitstatus = exitgen(self.__class__.__name__, int(status), 0)
        print("Api-v1 - Connectionstatus: " + str(exitstatus.json))
        return exitstatus

class device(Resource):
    def get(self):

        response = curl('get', '/v1/device?apikey=', '')

        print("Api-v1 - Device: Device data returned.")

        return response.json()

class healthcheck(Resource):
        def get(self):
            return "ok"

class hostconfig(Resource):
    def get(self, hostname):

        response = curl('patch', '/v1/device/host-config?apikey=', '{"network": {"hostname": "%s"}}'%(hostname))
            
        exitstatus = exitgen(self.__class__.__name__, int(response.status_code), hostname)
        print("Api-v1 - Hostconfig: " + str(exitstatus.json))
        return exitstatus

class journallogs(Resource):
    def get(self):

        response = curl('post', '/v2/journal-logs?apikey=', '("follow", "false", "all", "true", "format", "short")')

        print("Api-v1 - Journald-logs: Available logs returned.")

        return response.text

class update(Resource):
    def get(self):

        response = curl('post', '/v1/update?apikey=', '("force", "true")')

        exitstatus = make_response(response.text, response.status_code)

        print("Api-v1 - Update: " + exitstatus.data.decode("utf-8"), exitstatus.status_code)

        return exitstatus

class uuid(Resource):
    def get(self):
        uuid = os.popen('printenv BALENA_DEVICE_UUID').read().strip()

        response = make_response(jsonify(
                    {"UUID": uuid}), 200)
        print("Api-v1 - UUID: Device UUID returned.")
        return response

class wififorget(Resource):
    def get(self):

        status = 500
        checkconnection = connectionstatus().get()
    
        if checkconnection.status_code == 200:
            
            currentssid = os.popen('iwgetid -r').read().strip()
            connections = NetworkManager.Settings.ListConnections()

            for connection in connections:
                if connection.GetSettings()["connection"]["type"] == "802-11-wireless":
                    if connection.GetSettings()["802-11-wireless"]["ssid"] == currentssid:
                        print("Api-v1 - Wififorget: Deleting connection "
                            + connection.GetSettings()["connection"]["id"]
                        )

                        connection.Delete()
                        status = 200

            time.sleep(5)
            
            startwifi = launchwifi()

            if startwifi.status_code != 200:
                status = 500

        else:
            status = 409

        exitstatus = exitgen(self.__class__.__name__, int(status), 0)

        print("Api-v1 - Wififorget: " + str(exitstatus.json)) 
        return exitstatus

class wififorgetall(Resource):
    def get(self):
        status = 204
        checkconnection = connectionstatus().get()
        connections = NetworkManager.Settings.ListConnections()

        for connection in connections:
            if connection.GetSettings()["connection"]["type"] == "802-11-wireless":
                print("Api-v1 - Wififorgetall: Deleting connection "
                    + connection.GetSettings()["connection"]["id"]
                )
                connection.Delete()
                status = 200
                
        if checkconnection.status_code == 200 and status == 200:
            time.sleep(5)
            
            startwifi = launchwifi()

            if startwifi.status_code != 200:
                status = 500

        else:
            status = 500

        exitstatus = exitgen(self.__class__.__name__, int(status), 0)

        print("Api-v1 - Wififorgetall: " + str(exitstatus.json)) 
        return exitstatus

containerhostname = os.popen('hostname').read().strip()
devicehostname = curl('get', '/v1/device/host-config?apikey=', '')

if containerhostname != devicehostname.json()["network"]["hostname"]:
    print("Container hostname and device hostname do not match. Likely a hostname" + \
    "change has been performed. Balena Supervisor should detect this and rebuild " + \
    "the container shortly. Waiting 90 seconds before continuing anyway.")
    time.sleep(90)

connected = os.popen('iwgetid -r').read().strip()
if connected:
    start = update().get()
    print("Api-v1 - API Started - Device connected to local wifi")
else:
    start = launchwifi()
    print("Api-v1 - API Started - Controller launched")

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