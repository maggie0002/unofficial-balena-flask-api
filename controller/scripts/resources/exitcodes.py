from flask import jsonify, make_response
import resources.config, resources.globals

def exitgen(*args):
    if args[0] == 'connectionstatus':

        if args[1] == 200:

            ecode = make_response(
                jsonify(
                    {"status": args[1]},
                        {"data": {
                            "status": "connected",
                            "message": "The device is connected to a wifi network.",
                            "command": args[0]
                        }
                    }
                ), args[1])

        elif args[1] == 206:

            ecode = make_response(
                jsonify(
                    {"status": args[1]},
                        {"data": {
                            "status": "disconnected",
                            "message": "The device is not connected to a wifi network.",
                            "command": args[0]
                        }
                    }
                ), args[1],)

        elif args[1] == 500:

            ecode = make_response(
                jsonify(
                    {"status": args[1]},
                        {"data": {
                            "status": "error",
                            "message": "The device is not connected to a wifi network, but the wifi-connect interface is not up. User needs to try again, or restart the device.",
                            "command": args[0]
                        }
                    }
                ), args[1])

        else:
            ecode = "Unrecognised error args[1]"

    if args[0] == 'hostconfig':
        if args[1] == 200:
            ecode = make_response(
                jsonify(
                    {"status": args[1]},
                        {"data": {
                            "status": "success",
                            "hostname": args[2],
                            "message": "The hostname was updated.",
                            "command": args[0]
                        }
                    }
                ), args[1])

        else:
            ecode = make_response(
                jsonify(
                    {"status": args[1]},
                        {"data": {
                            "status": "error",
                            "hostname": args[2],
                            "message": "The hostname could not be updated.",
                            "command": args[0]
                        }
                    }
                ), args[1])

    if args[0] == 'wififorget' or args[0] == 'wififorgetall':

        if args[1] == 202:
            ecode = make_response(
                jsonify(
                    {"status": args[1]},
                        {"data": {
                            "status": "accepted",
                            "message": "Reset request sent.",
                            "command": args[0]
                        }
                    }
                ), args[1]
            )

        elif args[1] == 409: 
            ecode = make_response(
                jsonify(
                    {"status": args[1]},
                        {"data": {
                            "status": "conflict",
                            "message": "The device is not connected. No action taken.",
                            "command": args[0]
                        }
                    }
                ), args[1]
            )

        else:
            ecode = "Unrecognised error args[1]"

    if args[0] == 'forget' or args[0] == 'forgetall':

        if args[1] == 204:

            ecode = make_response(
                jsonify(
                    {"status": args[1]},
                        {"data": {
                            "status": "empty",
                            "message": "There were no wifi-connections to delete.",
                            "command": args[0]
                        }
                    }
                ), args[1])            

        elif args[1] == 409:

            ecode = make_response(
                jsonify(
                    {"status": args[1]},
                        {"data": {
                            "status": "conflict",
                            "message": "No connection found to delete.",
                            "command": args[0]
                        }
                    }
                ), args[1])

        elif args[1] == 500:

            ecode = make_response(
                jsonify(
                    {"status": args[1]},
                        {"data": {
                            "status": "error",
                            "message": "Failed to start wifi-connect.",
                            "command": args[0]
                        }
                    }
                ), args[1])

        elif args[1] == 200:

            ecode = make_response(
                jsonify(
                    {"status": args[1]},
                        {"data": {
                            "status": "success",
                            "message": "The connection was reset.",
                            "command": args[0]
                        }
                    }
                ), args[1])

        else:
            ecode = "Unrecognised error args[1]"

    return ecode