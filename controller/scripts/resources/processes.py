import resources.config, resources.globals
import NetworkManager, requests, time, subprocess, sys

#Handle exiting with soft wifi-connect shutdown
def handle_exit(*args):

    try:
        try:
            global wifip
            wifip.terminate()
            wifip.communicate(timeout=10)
        except Exception:
            wifip.kill()
    except Exception as ex:
        print("Wifi-connect was already down. " + str(ex))
    print("Finshed the exit process")
    sys.exit(0)

def curl(supretries=8, timeout=1, **cmd):

    #Check Balena Supervisor is ready
    retry = 1

    while True:
        try:
            supervisorstatus = requests.get(
                f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}/ping',
                headers={"Content-Type": "application/json"}, timeout=timeout
            ) 

            if supervisorstatus.status_code == 200:
                break
            else:
                class supervisorerror:
                    text = f'Supervisor returned error code {supervisorstatus.status_code}'
                    status_code = 500
                return supervisorerror

        except Exception as ex:
            print("Waiting for Balena Supervisor to be ready. Retry " + str(retry) + str(ex))
        
            if retry == supretries:

                class supervisortimeout:
                    text = ex
                    status_code = 408
                return supervisortimeout
            
            time.sleep(2)
            retry = retry + 1

    #Process curl request 
    try: 
        if cmd["method"] == 'post':
            response = requests.post(
                f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}{cmd["path"]}{resources.globals.BALENA_SUPERVISOR_API_KEY}',
                json=[cmd["string"]],
                headers={"Content-Type": "application/json"}, timeout=timeout
            )

        elif cmd["method"] == 'patch':

            response = requests.patch(
                f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}{cmd["path"]}{resources.globals.BALENA_SUPERVISOR_API_KEY}',
                data=cmd["string"],
                headers={"Content-Type": "application/json"}, timeout=timeout
            )

        elif cmd["method"] == 'get':

            response = requests.get(
                f'{resources.globals.BALENA_SUPERVISOR_ADDRESS}{cmd["path"]}{resources.globals.BALENA_SUPERVISOR_API_KEY}',
                headers={"Content-Type": "application/json"}, timeout=timeout
            )
    except Exception as ex:
        print("Curl request timed out. " + str(ex))
        class curlstatus:
            text = ex
            status_code = 408
        return curlstatus

    return response

class wifi:

    def checkconnection():

        run = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True).stdout.rstrip()

        if run:
            return {'wificonnectionstatus': 'connected', 'status': 200}, 200
        else:
            return {'wificonnectionstatus': 'not connected', 'status': 206}, 206

    def forget():
        
        status = 1
        
        #Wait so user gets return code before disconnecting
        time.sleep(5)

        wificonnect().stop()

        #Get the name of the current wifi network
        currentssid = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True).stdout.rstrip()

        #Get a list of all connections
        connections = NetworkManager.Settings.ListConnections()

        for connection in connections:
            if connection.GetSettings()["connection"]["type"] == "802-11-wireless":
                if connection.GetSettings()["802-11-wireless"]["ssid"] == currentssid:
                    print("Wififorget: Deleting connection "
                        + connection.GetSettings()["connection"]["id"]
                    )

                    #Delete the identified connection and change status code to 0 (success)
                    connection.Delete()
                    status = 0

        #Check that a connection was deleted
        if status == 1:
            print('Failed to delete connection, trying to clear all saved connections and continuing.')
            wifi.forgetall()

        #Wait before trying to launch wifi-connect
        time.sleep(2)

        wifimessage, wifistatuscode = wificonnect().start()

        #If wifi-connect didn't launch, change status code to 500 (internal server error)
        try:
            if wifistatuscode != 200:
                print(str(wifimessage) + str(wifistatuscode))
                return wifimessage, wifistatuscode
        except Exception as ex:
            print("Wifi connect failed to launch. " + str(ex))
            return "Wifi connect failed to launch"

        print('Success, connection deleted.')
        return 200

    def forgetall():

        #Wait so user gets return code before disconnecting
        time.sleep(5)

        wificonnect().stop()

        #Get a list of all connections
        connections = NetworkManager.Settings.ListConnections()

        for connection in connections:
            if connection.GetSettings()["connection"]["type"] == "802-11-wireless":
                print("Deleting connection "
                    + connection.GetSettings()["connection"]["id"]
                )

                #Delete the identified connection and change status code to 200 (success)
                connection.Delete()

        #Wait before trying to launch wifi-connect
        time.sleep(2)

        wifimessage, wifistatuscode = wificonnect().start()

        #If wifi-connect didn't launch, change status code to 500 (internal server error)
        try:
            if wifistatuscode != 200:
                print(str(wifimessage) + str(wifistatuscode))
                return wifimessage, wifistatuscode
        except Exception as ex:
            print("Wifi connect failed to launch. " + str(ex))
            return "Wifi connect failed to launch"
        
        print('Success, all wi-fi connections deleted, wifi-connect started.')
        return 200

class wificonnect:
    def start(self):
        
        global wifip

        #Check default hostname variables is not empty, and set if it is
        try:
            resources.config.defaulthostname
        except Exception:
            resources.config.defaulthostname = 'defaulthostname'

        #Get the current hostname of the container, and set a default on failure
        try:
            currenthostname = subprocess.run(["hostname"], capture_output=True, text=True).stdout.rstrip()
        except Exception:
            currenthostname = resources.config.deafultssid

        #Check the current hostname variable is not empty, and set if it is
        try:
            currenthostname
        except Exception:
            currenthostname = resources.config.deafultssid

        #Decide whether to use default SSID or match hostname
        if currenthostname == resources.config.defaulthostname:
            cmd = f'/app/common/wifi-connect/wifi-connect -s {resources.config.deafultssid} -o 8080 --ui-directory /app/common/wifi-connect/custom-ui'.split()
        else:
            cmd = f'/app/common/wifi-connect/wifi-connect -s {currenthostname} -o 8080 --ui-directory /app/common/wifi-connect/custom-ui'.split()

        wifip = subprocess.Popen(cmd)
        time.sleep(4)

        if not wifip.poll() == None:
            return {'wifilaunch': 'Wifi-Connect launch failure.', 'status': 500}, 500

        return {'wifilaunch': 'success', 'status': 200}, 200

    def stop(self):
        
        global wifip

        try:
            wifipoll = wifip.poll()
        except Exception:
            print("wifi-connect not started")
            return 1

        if wifipoll != None:

            print("wifi-connect already stopped")
            return 1

        try:
            wifip.terminate()
            wifip.communicate(timeout=10)
        except Exception:
            wifip.kill()

        return 0

    def status(self):

        global wifip
        
        try:
            curlwifi = requests.get('http://192.168.42.1:8080', timeout=1)
            if curlwifi.status_code == 200:
                curlwifi = "up"
            else:
                curlwifi = "down"
        except Exception:
            curlwifi = "down"

        try:
            wifipoll = wifip.poll()
        except Exception:
            wifipoll = "down"   

        if curlwifi == "up" and wifipoll == None:
            return 0

        elif curlwifi == "down" and wifipoll != None:
            return 1

        else: 
            return 500