from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
import os, requests, NetworkManager, time, socket, subprocess

app = Flask(__name__)

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

    return str(response.status_code), str(response.text)
    
def exitgen(process, code, hostname):
    with app.app_context():
        if process == 'connectionstatus':

            if code == 200:

                ecode = make_response(
                    jsonify(
                        {"status": code},
                            {"data": {
                                "status": "connected",
                                "message": "The device is connected to a wifi network.",
                                "command": process
                            }
                        }
                    ), code)

            elif code == 206:

                ecode = make_response(
                    jsonify(
                        {"status": code},
                            {"data": {
                                "status": "disconnected",
                                "message": "The device is not connected to a wifi network.",
                                "command": process
                            }
                        }
                    ), code,)

            elif code == 500:

                ecode = make_response(
                    jsonify(
                        {"status": code},
                            {"data": {
                                "status": "error",
                                "message": "The wifi is not connected to a router, but the wifi-connect interface isn’t up. User needs to try again, or restart the device. ",
                                "command": process
                            }
                        }
                    ), code)

            else:
                ecode = "Unrecognised error code"

        if process == 'hostconfig':
            if code == 200:
                ecode = make_response(
                    jsonify(
                        {"status": code},
                            {"data": {
                                "status": "success",
                                "new-hostname": hostname,
                                "message": "The hostname was updated.",
                                "command": process
                            }
                        }
                    ), code)

            else:
                print(hostname)
                ecode = make_response(
                    jsonify(
                        {"status": code},
                            {"data": {
                                "status": "error",
                                "new-hostname": hostname,
                                "message": "The hostname could not be updated.",
                                "command": process
                            }
                        }
                    ), code)

        if process == 'wifireset':

            if code == 409:

                ecode = make_response(
                    jsonify(
                        {"status": code},
                            {"data": {
                                "status": "conflict",
                                "message": "The device is already disconnected, cannot be reset.",
                                "command": process
                            }
                        }
                    ), code)

            elif code == 500:

                ecode = make_response(
                    jsonify(
                        {"status": code},
                            {"data": {
                                "status": "error",
                                "message": "The device is connected but could not reset the connection.",
                                "command": process
                            }
                        }
                    ), code)

            elif code == 200:

                ecode = make_response(
                    jsonify(
                        {"status": code},
                            {"data": {
                                "status": "success",
                                "message": "The connection was reset.",
                                "command": process
                            }
                        }
                    ), code)

            else:
                ecode = "Unrecognised error code"

    return ecode

def launchwifi():
    currenthostname = socket.gethostname()
    if currenthostname == 'your-app-name':
        cmd = '/app/wifi-connect -s your-app-name -o 8080 --ui-directory custom-ui'.split()
    else:
        cmd = f'/app/wifi-connect -s your-app-name-{str(currenthostname)[-2:]} -o 8080 --ui-directory custom-ui'.split()

    p = subprocess.Popen(cmd, stdout = subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE)
    print("Api-v1 - Launchwifi: Wifi-Connect launched.")
    return str(p.returncode)

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

class hostconfig(Resource):
    def get(self, hostname):

        status, text = curl('patch', '/v1/device/host-config?apikey=', '{"network": {"hostname": "%s"}}'%(hostname))
            
        exitstatus = exitgen(self.__class__.__name__, int(status), hostname)
        print("Api-v1 - Hostconfig: " + str(exitstatus.json))
        return exitstatus

class journallogs(Resource):
    def get(self):

        status, text = curl('post', '/v2/journal-logs?apikey=', '("follow", "false", "all", "true", "format", "short")')

        print("Api-v1 - Journald-logs: Available logs returned.")

        return text

class update(Resource):
    def get(self):

        status, text = curl('post', '/v1/update?apikey=', '("force", "true")')

        exitstatus = make_response(text, status)

        print("Api-v1 - Update: " + str(exitstatus.json))

        return exitstatus

class wifireset(Resource):
    def get(self):

        status = 500
        checkconnection = connectionstatus().get()
    
        if checkconnection == 0:
            
            currentssid = os.popen('iwgetid -r').read().strip()
            connections = NetworkManager.Settings.ListConnections()

            for connection in connections:
                if connection.GetSettings()["connection"]["type"] == "802-11-wireless":
                    if connection.GetSettings()["802-11-wireless"]["ssid"] == currentssid:

                        status = 200
                        connection.Delete()

            time.sleep(15)
            
            startwifi = launchwifi()

            if startwifi != 200:
                exitstatus = 500

        elif checkconnection == 1:
            status = 409

        exitstatus = exitgen(self.__class__.__name__, int(status), 0)

        print("Api-v1 - Wifireset: " + str(exitstatus.json)) 
        return exitstatus

connected = connectionstatus().get()
if connected == 200:
    time.sleep(15)
    start = update().get()
    print("Api-v1 - API Started - Online")
else:
    start = launchwifi()
    print("Api-v1 - API Started - Offline")

if __name__ == '__main__':
    api.add_resource(connectionstatus, '/v1/connectionstatus')
    api.add_resource(hostconfig, '/v1/hostconfig/<hostname>') 
    api.add_resource(journallogs, '/v1/journallogs')
    api.add_resource(update, '/v1/update')
    api.add_resource(wifireset, '/v1/wifireset')

    app.run(port=9090,host='0.0.0.0')