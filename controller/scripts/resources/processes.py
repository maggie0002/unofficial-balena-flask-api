import resources.config, resources.globals
import os, requests, NetworkManager, time, subprocess

def checkconnection():

    run = os.popen('iwgetid -r').read().strip()

    if run:
        #Device is connected to wifi
        return {'connectionstatus': 'connected'}, 200
    else:
        pingwifi = os.system('ping -c 1 -w 1 -I wlan0 192.168.42.1 >/dev/null 2>&1')

        if pingwifi == 0:
            #Device is not connected to wifi
            return {'connectionstatus': 'not connected'}, 206
        else:
            #Device is not connected to a wifi network, but the wifi-connect interface isn’t up.
            return {'connectionstatus': 'wifi-connect failure'}, 500

def curl(**cmd):

    #Check Balena Supervisor is ready
    retry = 1

    if not hasattr(cmd, 'timeout'):
        cmd["timeout"] = 3
    if not hasattr(cmd, 'supretries'):
        cmd["supretries"] = 4

    while True:
        
        supervisorstatus = requests.get(
            f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}/ping',
            headers={"Content-Type": "application/json"}, timeout=1
        ) 

        if supervisorstatus == 200:
            break

        if retry == cmd["supretries"]:
            return supervisorstatus
            
        print("Api-v1 - Waiting for Balena Supervisor to be ready. Retry " + retry)
        time.sleep(1)
        retry = retry + 1

    #Process curl request 
    if cmd["method"] == 'post':
        response = requests.post(
            f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}{cmd["path"]}{resources.globals.BALENA_SUPERVISOR_API_KEY}',
            json=[cmd["string"]],
            headers={"Content-Type": "application/json"}, timeout=cmd["timeout"]
        )

    elif cmd["method"] == 'patch':

        response = requests.patch(
            f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}{cmd["path"]}{resources.globals.BALENA_SUPERVISOR_API_KEY}',
            data=cmd["string"],
            headers={"Content-Type": "application/json"}, timeout=cmd["timeout"]
        )

    elif cmd["method"] == 'get':

        response = requests.get(
            f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}{cmd["path"]}{resources.globals.BALENA_SUPERVISOR_API_KEY}',
            headers={"Content-Type": "application/json"}, timeout=cmd["timeout"]
        )

    return response

class wifi:
    def launch(self):
    
        try:
            pingwifi = os.system('ping -c 1 -w 1 -I wlan0 192.168.42.1 >/dev/null 2>&1')
        except:
            pingwifi = 1

        if pingwifi == 0:
            return {'wifi': 'Wifi-Connect already running'}, 500

        try:
            currenthostname = os.popen('hostname').read().strip()
        except:
            currenthostname = resources.config.deafultssid

        try:
            currenthostname
        except NameError:
            currenthostname = resources.config.deafultssid

        try:
            resources.config.defaulthostname
        except NameError:
            resources.config.defaulthostname = 'welcome'

        if currenthostname == resources.config.defaulthostname:
            cmd = f'/app/common/wifi-connect/wifi-connect -s {resources.config.deafultssid} -o 8080 --ui-directory /app/common/wifi-connect/custom-ui'.split()
        else:
            cmd = f'/app/common/wifi-connect/wifi-connect -s {currenthostname} -o 8080 --ui-directory /app/common/wifi-connect/custom-ui'.split()

        p = subprocess.Popen(cmd, stdout = subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE)

        if not p.returncode == None:
            return {'wifi': 'Wifi-Connect launch failure.'}, 500

        return {'wifi': 'success'}, 200

    def forget():

        #Wait so user gets return code before disconnecting
        time.sleep(5)

        #Get the name of the current wifi network
        currentssid = os.popen('iwgetid -r').read().strip()

        if not currentssid:
            return {'forget': 'No connection found to delete.'}, 409

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
                    status = 0

        #Check that a connection was deleted
        if not status:
            return {'forget': 'Failed to delete connection.'}, 500

        #Wait before trying to launch wifi-connect
        time.sleep(5)
        
        startwifi = wifi().launch()

        if startwifi != 200:
            return {'forget': 'Failed to start wifi-connect.'}, 500

        return {'wifi': 'success'}, 200

    def forgetall():

        #Wait so user gets return code before disconnecting
        time.sleep(5)

        #Check and store the current connection state
        _, connectionstate = checkconnection()

        #Get a list of all connections
        connections = NetworkManager.Settings.ListConnections()

        for connection in connections:
            if connection.GetSettings()["connection"]["type"] == "802-11-wireless":
                print("Api-v1 - Wififorgetall: Deleting connection "
                    + connection.GetSettings()["connection"]["id"]
                )

                #Delete the identified connection and change status code to 200 (success)
                connection.Delete()
                status = 0

        #If connection status when starting was 'connected' and a network has been deleted
        if connectionstate == 200 and status == 0:

            #Wait before trying to launch wifi-connect
            time.sleep(5)
            
            startwifi = wifi().launch()

            #If wifi-connect didn't launch, change status code to 500 (internal server error)
            if startwifi != 200:
                return {'forget': 'Failed to start wifi-connect.'}, 500

        #Or if connection status when starting was 'connected' and a network has not been deleted
        elif connectionstate == 200 and status != 200:
            #Set error code to 500, failed to delete the attached network
            return {'forget': 'Failed to delete the attached network.'}, 500

        return {'wifi': 'success'}, 200