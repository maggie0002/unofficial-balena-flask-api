from flask import make_response, jsonify
from flask_restful import Resource
from resources.processes import curl, wifi
from resources.exitcodes import exitgen
import resources.globals
import os, threading

class connectionstatus(Resource):
    def get(self):

        run = os.popen('iwgetid -r').read().strip()

        if run:
            #Device is connected to wifi
            status = 200
        else:
            pingwifi = os.system('ping -c 1 -w 1 -I wlan0 192.168.42.1 >/dev/null 2>&1')

            if pingwifi == 0:
                #Device is not connected to wifi
                status = 206
            else:
                #Device is not connected to a wifi network, but the wifi-connect interface isn’t up.
                status = 500

        exitstatus = exitgen(self.__class__.__name__, int(status))
        print("Api-v1 - Connectionstatus: " + str(exitstatus.json))
        return exitstatus

class device(Resource):
    def get(self):

        response = curl('get', '/v1/device?apikey=')

        print("Api-v1 - Device: Device data returned.")

        return response.json()

class healthcheck(Resource):
    def get(self):
        return "ok"

class hostconfig(Resource):
    def get(self, hostname):
        if hostname != None:
            response = curl('patch', '/v1/device/host-config?apikey=', '{"network": {"hostname": "%s"}}'%(hostname))
                
            exitstatus = exitgen(self.__class__.__name__, int(response.status_code), hostname)
            print("Api-v1 - Hostconfig: " + str(exitstatus.json))
        else:
            exitstatus = exitgen(self.__class__.__name__, 500, hostname)
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

        #Check and store the current connection state
        checkconnection = connectionstatus().get()

        #If the device is connected to a wifi network
        if checkconnection.status_code == 200:

            wififorget = threading.Thread(target=wifi.forget, name='wififorget')
            wififorget.start()
            status = 202

        else:
            
            status = 409
        
        exitstatus = exitgen(self.__class__.__name__, status)
        print("Api-v1 - Wififorget: Accepted")
        return exitstatus

class wififorgetall(Resource):
    def get(self):

        wififorgetall = threading.Thread(target=wifi.forgetall, name='wififorgetall')
        wififorgetall.start()
        status = 202
        
        exitstatus = exitgen(self.__class__.__name__, status)
        print("Api-v1 - Wififorget: Accepted")
        return exitstatus