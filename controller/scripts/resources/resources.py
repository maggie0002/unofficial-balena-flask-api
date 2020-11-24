from flask_restful import Resource
from werkzeug import serving
from resources.processes import curl, wifi
import resources.globals
import threading

#Disable logging for healthcheck
parent_log_request = serving.WSGIRequestHandler.log_request

def log_request(self, *args, **kwargs):
    if self.path == '/':
        return

    parent_log_request(self, *args, **kwargs)

class device(Resource):
    def get(self):

        response = curl(method = "get", 
                        path = "/v1/device?apikey=")

        return response["jsonresponse"], response["status_code"]

class healthcheck(Resource):
    def get(self):
        
        serving.WSGIRequestHandler.log_request = log_request
        return {'status': 200, 'message': 'ok'}, 200

class hostconfig(Resource):
    def get(self, hostname):

        response = curl(method = "patch", 
                        path = "/v1/device/host-config?apikey=", 
                        string = '{"network": {"hostname": "%s"}}'%(hostname))

        return {
            'status': response["status_code"],
            'hostname': hostname,
            'message': response["text"]
        }, response["status_code"]

class journallogs(Resource):
    def get(self):

        response = curl(method = "post", 
                        path  = "/v2/journal-logs?apikey=", 
                        string = '("follow", "false", "all", "true", "format", "short")')

        return response["text"], response["status_code"]

class update(Resource):
    def get(self):

        response = curl(method ="post",
                        path = "/v1/update?apikey=", 
                        string = '("force", "true")')

        return {'status': response["status_code"], 'message': response["text"]}, response["status_code"]

class uuid(Resource):
    def get(self):

        return {'uuid': resources.globals.BALENA_DEVICE_UUID}

class wificonnectionstatus(Resource):
    def get(self):

        response = wifi().checkconnection()

        if response:
            return {'status': 200, 'message': 'connected'}, 200
        else:
            return {'status': 206, 'message': 'disconnected'}, 206

class wififorget(Resource):
    def get(self):

        #Check and store the current connection state
        connectionstate = wifi().checkconnection()

        #If the device is connected to a wifi network
        if not connectionstate:
            return {
                'status': 409,
                'message': 'Device is already disconnected, connection cannot be reset.'
            }, 409

        wififorget = threading.Thread(target=wifi.forget, name='wififorget')
        wififorget.start()

        return {'status': 202, 'message': 'Reset request sent.'}, 202  

class wififorgetall(Resource):
    def get(self):

        wififorgetall = threading.Thread(target=wifi.forgetall, name='wififorgetall')
        wififorgetall.start()

        return {'status': 202, 'message': 'Reset request sent.'}, 202