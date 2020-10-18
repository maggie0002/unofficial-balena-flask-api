from flask import jsonify, make_response

def exitgen(process, code, hostname):
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
                            "message": "The device is not connected to a wifi network, but the wifi-connect interface isn’t up. User needs to try again, or restart the device. ",
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
                            "hostname": hostname,
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
                            "hostname": hostname,
                            "message": "The hostname could not be updated.",
                            "command": process
                        }
                    }
                ), code)

    if process == 'wififorget' or process == 'wififorgetall':

        if code == 204:

            ecode = make_response(
                jsonify(
                    {"status": code},
                        {"data": {
                            "status": "empty",
                            "message": "There were no wifi-connections to delete.",
                            "command": process
                        }
                    }
                ), code)            

        if code == 409:

            ecode = make_response(
                jsonify(
                    {"status": code},
                        {"data": {
                            "status": "conflict",
                            "message": "The device is already disconnected. No action taken.",
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