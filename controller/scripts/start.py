from flask import Flask, request
from flask_restful import Resource, Api
import os, requests, NetworkManager, time, subprocess

app = Flask(__name__)

api = Api(app)

BALENA_SUPERVISOR_API_KEY = os.environ['BALENA_SUPERVISOR_API_KEY']
BALENA_SUPERVISOR_ADDRESS = os.environ['BALENA_SUPERVISOR_ADDRESS']

print("Api-v1: -Starting API...-")

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

    return str(response.status_code), str(response.text)

class connectionstatus(Resource):
    def get(self):

        run = os.popen('iwgetid -r').read().strip()
        print(run)

        if run:
             out = "up"
        else:

            curlwifi = os.system('ping -c 1 -w 1 -I wlan0 192.168.42.1 > /dev/null')

            if curlwifi == 0:
                out = "down"
            else:
                out = "error"
        
        print("Api-v1: -Connection Status- " + out)              

        return out

class hostconfig(Resource):
    def get(self, hostname):

        status, text = curl('patch', '/v1/device/host-config?apikey=', '{"network": {"hostname": "%s"}}'%(hostname))

        print("Api-v1: -Host-config- " + status, text)
        return status

class journallogs(Resource):
    def get(self):

        status, text = curl('post', '/v2/journal-logs?apikey=', '("follow", "false", "all", "true", "format", "short")')

        print("Api-v1: -Journald-logs- " + status + " - Journald logs sent to browser")
        return text

class launchwifi(Resource):
    def get(self):
        cmd = '/app/wifi-connect -o 8080 --ui-directory custom-ui'.split()

        p = subprocess.Popen(cmd, stdout = subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE)

        print("Api-v1: -WiFi Launch- " + p.returncode)

        return p.returncode

class update(Resource):
    def get(self):

        status, text = curl('post', '/v1/update?apikey=', '("force", "true")')

        print("Api-v1: -Update- " + status, text)
        return status

class wifireset(Resource):
    def get(self):

        checkconnection = connectionstatus().get()

        if checkconnection == "up":
            cleared = 1
            currentssid = os.popen('iwgetid -r').read().strip()
            connections = NetworkManager.Settings.ListConnections()

            for connection in connections:
                if connection.GetSettings()["connection"]["type"] == "802-11-wireless":
                    if connection.GetSettings()["802-11-wireless"]["ssid"] == currentssid:
                        print("Api-v1: -Wifi-reset- Deleting connection "
                            + connection.GetSettings()["connection"]["id"]
                        )
                        cleared = 0
                        connection.Delete()
            print("Api-v1: -Wifi-reset- Return code: " + str(cleared))

            time.sleep(15)
            
            startwifi = launchwifi().get()

            out = cleared, startwifi

        else:
            out = 3
            print("Api-v1: -API Started- ERROR - Already disconnected.")
        
        return out

connected = connectionstatus().get()
if connected == "up":
    time.sleep(15)
    start = update().get()
    print("Api-v1: -API Started- Online - Return code: " + str(start))
else:
    start = launchwifi().get()
    print("Api-v1: -API Started- Offline - Return code: " + str(start))

api.add_resource(connectionstatus, '/v1/connectionstatus')
api.add_resource(hostconfig, '/v1/hostconfig/<hostname>') 
api.add_resource(journallogs, '/v1/journallogs')
api.add_resource(update, '/v1/update')
api.add_resource(wifireset, '/v1/wifireset')

if __name__ == '__main__':
    app.run(port=9090,host='0.0.0.0')