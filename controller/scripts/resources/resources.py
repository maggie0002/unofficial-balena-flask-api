from flask_restful import Resource, abort
from werkzeug import serving
from resources.processes import checkconnection, curl, wifi
import resources.globals
import threading

#Disable logging for healthcheck
parent_log_request = serving.WSGIRequestHandler.log_request

def log_request(self, *args, **kwargs):
    if self.path == '/':
        return

    parent_log_request(self, *args, **kwargs)

class connectionstatus(Resource):
    def get(self):

        response, status_code = checkconnection()

        return response, status_code

class device(Resource):
    def get(self):

        response = curl(method = "get", path = "/v1/device?apikey=")

        return {'device': response.text, 'status': response.status_code}, response.status_code

class healthcheck(Resource):
    def get(self):
        
        serving.WSGIRequestHandler.log_request = log_request
        return {'healthcheck': 'ok', 'status': 200}, 200

class hostconfig(Resource):
    def get(self, hostname):

        try:
            hostname
        except NameError:
            abort(404, hostconfig='No hostname entered.', status=404)

        response = curl(method = "patch", path = "/v1/device/host-config?apikey=", string = '{"network": {"hostname": "%s"}}'%(hostname))

        return {'hostconfig': response.text, 'status': response.status_code}, response.status_code

class journallogs(Resource):
    def get(self):

        response = curl(method = "post", path  = "/v2/journal-logs?apikey=", string = '("follow", "false", "all", "true", "format", "short")', timeout = 10)

        return response.text

class update(Resource):
    def get(self):

        response = curl(method ="post", path = "/v1/update?apikey=", string = '("force", "true")')

        return {'update': response.text, 'status': response.status_code}, response.status_code

class uuid(Resource):
    def get(self):

        return {'uuid': resources.globals.BALENA_DEVICE_UUID}

class wififorget(Resource):
    def get(self):

        #Check and store the current connection state
        _, connectionstate = checkconnection()

        #If the device is connected to a wifi network
        if connectionstate != 200:
            abort(409, wififorget='The device is not connected. No action taken.', status=409) 

        wififorget = threading.Thread(target=wifi.forget, name='wififorget')
        wififorget.start()

        return {'wififorget': 'Reset request sent.', 'status': 202}, 202  

class wififorgetall(Resource):
    def get(self):

        wififorgetall = threading.Thread(target=wifi.forgetall, name='wififorgetall')
        wififorgetall.start()

        return {'wififorgetall': 'Reset request sent.', 'status': 202}, 202