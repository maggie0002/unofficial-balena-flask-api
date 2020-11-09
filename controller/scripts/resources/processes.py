import resources.config, resources.globals
import requests, NetworkManager, time, subprocess

def checkconnection():

    run = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True).stdout.rstrip()

    if run:
        return {'connectionstatus': 'connected', 'status': 200}, 200
    else:
        
        curlwifi = wifi().wificonnect()

        if curlwifi == 200:
            return {'connectionstatus': 'not connected', 'status': 206}, 206
        else:
            return {'connectionstatus': 'Device is not connected to a wifi network, but the wifi-connect interface isn’t up', 'status': 409}, 409

def curl(**cmd):

    #Check Balena Supervisor is ready
    retry = 1

    if not hasattr(cmd, 'timeout'):
        cmd["timeout"] = 3
    if not hasattr(cmd, 'supretries'):
        cmd["supretries"] = 4

    while True:
        try:
            supervisorstatus = requests.get(
                f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}/ping',
                headers={"Content-Type": "application/json"}, timeout=1
            ) 

            if supervisorstatus.status_code == 200:
                break
            else:
                class supervisorerror:
                    text = "Supervisor returned error code"
                    status_code = 500
                return supervisorerror

        except requests.exceptions.Timeout:
            print("Api-v1 - Waiting for Balena Supervisor to be ready. Retry " + str(retry))
        
            if retry == cmd["supretries"]:

                class supervisortimeout:
                    text = "Supervisor Timeout"
                    status_code = 408
                return supervisortimeout
            
            time.sleep(4)
            retry = retry + 1

    #Process curl request 
    try: 
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
    except requests.exceptions.Timeout:
        class curlstatus:
            text = "Supervisor Timeout"
            status_code = 408
        return curlstatus

    return response

class wifi:
    def launch(self):
        
        #Check if wifi-connect is already up
        try:
            curlwifi = wifi().wificonnect()
        except:
            curlwifi = 0
            
        if curlwifi == 200:
            return {'wifilaunch': 'Wifi-Connect already running', 'status': 500}, 500

        #Check default hostname variables is not empty, and set if it is
        try:
            resources.config.defaulthostname
        except NameError:
            resources.config.defaulthostname = 'defaulthostname'

        #Get the current hostname of the container, and set a default on failure
        try:
            currenthostname = subprocess.run(["hostname"], capture_output=True, text=True).stdout.rstrip()
        except:
            currenthostname = resources.config.deafultssid

        #Check the current hostname variable is not empty, and set if it is
        try:
            currenthostname
        except NameError:
            currenthostname = resources.config.deafultssid

        #Decide whether to use default SSID or match hostname
        if currenthostname == resources.config.defaulthostname:
            cmd = f'/app/common/wifi-connect/wifi-connect -s {resources.config.deafultssid} -o 8080 --ui-directory /app/common/wifi-connect/custom-ui'.split()
        else:
            cmd = f'/app/common/wifi-connect/wifi-connect -s {currenthostname} -o 8080 --ui-directory /app/common/wifi-connect/custom-ui'.split()

        p = subprocess.Popen(cmd, stdout = subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE)

        if not p.returncode == None:
            return {'wifilaunch': 'Wifi-Connect launch failure.', 'status': 500}, 500

        return {'wifilaunch': 'success', 'status': 200}, 200

    def forget():

        #Wait so user gets return code before disconnecting
        time.sleep(5)

        #Get the name of the current wifi network
        currentssid = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True).stdout.rstrip()

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
            print({'wififorget': 'Failed to delete connection.', 'status': 500}, 500)
            return {'wififorget': 'Failed to delete connection.', 'status': 500}, 500

        #Wait before trying to launch wifi-connect
        time.sleep(5)

        wifimessage, wifistatuscode = wifi().launch()

        if wifistatuscode != 200:
            print('Api-v1 - wififorget - ' + str(wifimessage) + str(wifistatuscode))
            return {'wififorget': 'Failed to start wifi-connect', 'status': wifistatuscode}, wifistatuscode

        print({'wififorget': 'success', 'status': 200}, 200)
        return {'wififorget': 'success', 'status': 200}, 200

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

            wifimessage, wifistatuscode = wifi().launch()

            #If wifi-connect didn't launch, change status code to 500 (internal server error)
            if wifistatuscode != 200:
                print('Api-v1 - wififorgetall - ' + str(wifimessage) + str(wifistatuscode))
                return {'wififorgetall': 'Failed to start wifi-connect', 'status': wifistatuscode}, wifistatuscode

        #Or if connection status when starting was 'connected' and a network has not been deleted
        elif connectionstate == 200 and status != 200:
            #Set error code to 500, failed to delete the attached network
            print({'wififorgetall': 'Failed to delete the attached network.', 'status': 500}, 500)
            return {'wififorgetall': 'Failed to delete the attached network.', 'status': 500}, 500
        
        print({'wififorgetall': 'success', 'status': 200}, 200)
        return {'wififorgetall': 'success', 'status': 200}, 200

    def wificonnect(self):

        try:
            curlwifi = requests.get('http://192.168.42.1:8080', timeout=2)
        except requests.exceptions.Timeout:
            return 408

        return curlwifi.status_code