from flask import make_response
from resources.exitcodes import exitgen
import resources.config, resources.globals
import os, requests, NetworkManager, time, subprocess

def curl(*args):

    if args[0] == 'post':
        response = requests.post(
            f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}{args[1]}{resources.globals.BALENA_SUPERVISOR_API_KEY}',
            json=[args[2]],
            headers={"Content-Type": "application/json"},
        )

    elif args[0] == 'patch':

        response = requests.patch(
            f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}{args[1]}{resources.globals.BALENA_SUPERVISOR_API_KEY}',
            data=args[2],
            headers={"Content-Type": "application/json"},
        )

    elif args[0] == 'get':

        response = requests.get(
            f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}{args[1]}{resources.globals.BALENA_SUPERVISOR_API_KEY}',
            headers={"Content-Type": "application/json"},
        )

    return response 

class wifi:
    def launch(self):
        with resources.globals.app.app_context():
            pingwifi = os.system('ping -c 1 -w 1 -I wlan0 192.168.42.1 >/dev/null 2>&1')

            if pingwifi != 0:

                currenthostname = curl('get', '/v1/device/host-config?apikey=')
                if currenthostname.json()["network"]["hostname"]:
                    if currenthostname.json()["network"]["hostname"] == resources.config.defaulthostname:
                        cmd = f'/app/common/wifi-connect/wifi-connect -s {resources.config.deafultssid} -o 8080 --ui-directory /app/common/wifi-connect/custom-ui'.split()
                    else:
                        cmd = f'/app/common/wifi-connect/wifi-connect -s {currenthostname.json()["network"]["hostname"]} -o 8080 --ui-directory /app/common/wifi-connect/custom-ui'.split()

                    p = subprocess.Popen(cmd, stdout = subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            stdin=subprocess.PIPE)

                    if p.returncode == None:
                        exitstatus = make_response("Api-v1 - Wifi.Launch: Wifi-Connect launched.", 200)
                    else:
                        exitstatus = make_response("Api-v1 - Wifi.Launch: Wifi-Connect launch failure.", 500)

                    print(exitstatus.data.decode("utf-8"), exitstatus.status_code)

                else:
                    print("Api-v1 - Wifi.Launch: Hostname is blank. This is a fatal error.")
                    exitstatus = make_response("Hostname is blank. This is a fatal error.", 500)

            else:
                exitstatus = make_response("Api-v1 - Wifi.Launch: Wifi-Connect already running.", 500)

            return exitstatus

    def forget():
        with resources.globals.app.app_context():
            #Wait so user gets return code before disconnecting
            time.sleep(5)

            #Set default status to 409 unless action taken below
            status = 409

            #Get the name of the current wifi network
            currentssid = os.popen('iwgetid -r').read().strip()

            if currentssid:

                #Get a list of all connections
                connections = NetworkManager.Settings.ListConnections()

                for connection in connections:
                    if connection.GetSettings()["connection"]["type"] == "802-11-wireless":
                        if connection.GetSettings()["802-11-wireless"]["ssid"] == currentssid:
                            print("Api-v1 - Wififorget: Deleting connection "
                                + connection.GetSettings()["connection"]["id"]
                            )

                            #Delete the identified connection and change status code to 200 (success)
                            connection.Delete()
                            status = 200

            #If wifi-connect didn't launch, change status code to 500 (internal server error)
            if status == 200:
                #Wait before trying to launch wifi-connect
                time.sleep(5)
                
                startwifi = wifi().launch()

                if startwifi.status_code != 200:
                    status = 500

            exitstatus = exitgen("forget", int(status))

            print(exitstatus.data.decode("utf-8"), exitstatus.status_code)
            return exitstatus

    def forgetall():
        with resources.globals.app.app_context():
            #Wait so user gets return code before disconnecting
            time.sleep(5)

            #Set default status to 204 (nothing to delete)
            status = 204

            #Check and store the current connection state
            checkconnection = resources.resources.connectionstatus().get()

            #Get a list of all connections
            connections = NetworkManager.Settings.ListConnections()

            for connection in connections:
                if connection.GetSettings()["connection"]["type"] == "802-11-wireless":
                    print("Api-v1 - Wififorgetall: Deleting connection "
                        + connection.GetSettings()["connection"]["id"]
                    )

                    #Delete the identified connection and change status code to 200 (success)
                    connection.Delete()
                    status = 200

            #If connection status when starting was 'connected' and a network has been deleted
            if checkconnection.status_code == 200 and status == 200:

                #Wait before trying to launch wifi-connect
                time.sleep(5)
                
                startwifi = wifi().launch()

                #If wifi-connect didn't launch, change status code to 500 (internal server error)
                if startwifi.status_code != 200:
                    status = 500

            #Or if connection status when starting was 'connected' and a network has not been deleted
            elif checkconnection.status_code == 200 and status != 200:
                #Set error code to 500, failed to delete the attached network
                status = 500

            exitstatus = exitgen("forgetall", int(status))

            print("Api-v1 - Wififorgetall: " + str(exitstatus.json)) 
            return exitstatus