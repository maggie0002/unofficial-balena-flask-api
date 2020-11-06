from flask import abort
from flask_restful import Resource
from resources.processes import checkconnection, curl, wifi
import resources.globals
import os, threading

class connectionstatus(Resource):
    def get(self):

        return checkconnection()

class device(Resource):
    def get(self):

        response = curl('get', '/v1/device?apikey=', 5)

        return response.json(), response.statuscode

class healthcheck(Resource):
    def get(self):
        return {'status':'ok'}, 200

class hostconfig(Resource):
    def get(self, hostname):
        if hostname == None:
            abort(404, 'No hostname entered') 

        response = curl('patch', '/v1/device/host-config?apikey=', '{"network": {"hostname": "%s"}}'%(hostname), 5)

        return response.json(), response.statuscode

class journallogs(Resource):
    def get(self):

        response = curl('post', '/v2/journal-logs?apikey=', '("follow", "false", "all", "true", "format", "short")', 10)

        return response.text

class update(Resource):
    def get(self):

        response = curl('post', '/v1/update?apikey=', '("force", "true")', 5)

        return {'update': response.text}, response.status_code

class uuid(Resource):
    def get(self):
        uuid = os.popen('printenv BALENA_DEVICE_UUID').read().strip()

        return {'uuid': uuid}

class wififorget(Resource):
    def get(self):

        #Check and store the current connection state
        _, connectionstate = checkconnection()

        #If the device is connected to a wifi network
        if connectionstate != 200:
            abort(409, 'The device is not connected. No action taken.') 

        wififorget = threading.Thread(target=wifi.forget, name='wififorget')
        wififorget.start()

        return {'wififorget': 'Reset request sent.'}, 202  

class wififorgetall(Resource):
    def get(self):

        wififorgetall = threading.Thread(target=wifi.forgetall, name='wififorgetall')
        wififorgetall.start()

        return {'wififorget': 'Reset request sent.'}, 202