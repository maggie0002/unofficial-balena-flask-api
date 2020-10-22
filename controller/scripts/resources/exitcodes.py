from flask import jsonify, make_response

def exitgen(*args):
    if args[1] == 'connectionstatus':

        if args[2] == 200:

            ecode = make_response(
                jsonify(
                    {"status": args[2]},
                        {"data": {
                            "status": "connected",
                            "message": "The device is connected to a wifi network.",
                            "command": args[1]
                        }
                    }
                ), args[2])

        elif args[2] == 206:

            ecode = make_response(
                jsonify(
                    {"status": args[2]},
                        {"data": {
                            "status": "disconnected",
                            "message": "The device is not connected to a wifi network.",
                            "command": args[1]
                        }
                    }
                ), args[2],)

        elif args[2] == 500:

            ecode = make_response(
                jsonify(
                    {"status": args[2]},
                        {"data": {
                            "status": "error",
                            "message": "The device is not connected to a wifi network, but the wifi-connect interface isn’t up. User needs to try again, or restart the device. ",
                            "command": args[1]
                        }
                    }
                ), args[2])

        else:
            ecode = "Unrecognised error args[2]"

    if args[1] == 'hostconfig':
        if args[2] == 200:
            ecode = make_response(
                jsonify(
                    {"status": args[2]},
                        {"data": {
                            "status": "success",
                            "hostname": args[3],
                            "message": "The hostname was updated.",
                            "command": args[1]
                        }
                    }
                ), args[2])

        else:
            print(args[3])
            ecode = make_response(
                jsonify(
                    {"status": args[2]},
                        {"data": {
                            "status": "error",
                            "hostname": args[3],
                            "message": "The hostname could not be updated.",
                            "command": args[1]
                        }
                    }
                ), args[2])

    if args[1] == 'wififorget' or args[1] == 'wififorgetall':

        if args[2] == 202:
            ecode = make_response(
                jsonify(
                    {"status": args[2]},
                        {"data": {
                            "status": "accepted",
                            "message": "Reset request sent.",
                            "command": args[1]
                        }
                    }
                ), args[2]
            )

        elif args[2] == 409: 
            ecode = make_response(
                jsonify(
                    {"status": args[2]},
                        {"data": {
                            "status": "conflict",
                            "message": "The device is already disconnected. No action taken.",
                            "command": args[1]
                        }
                    }
                ), args[2]
            )

        else:
            ecode = "Unrecognised error args[2]"

    if args[1] == 'wififorgetrun' or args[1] == 'wififorgetallrun':

        if args[2] == 204:

            ecode = make_response(
                jsonify(
                    {"status": args[2]},
                        {"data": {
                            "status": "empty",
                            "message": "There were no wifi-connections to delete.",
                            "command": args[1]
                        }
                    }
                ), args[2])            

        elif args[2] == 409:

            ecode = make_response(
                jsonify(
                    {"status": args[2]},
                        {"data": {
                            "status": "conflict",
                            "message": "The device is already disconnected. No action taken.",
                            "command": args[1]
                        }
                    }
                ), args[2])

        elif args[2] == 500:

            ecode = make_response(
                jsonify(
                    {"status": args[2]},
                        {"data": {
                            "status": "error",
                            "message": "Could not reset the connection.",
                            "command": args[1]
                        }
                    }
                ), args[2])

        elif args[2] == 200:

            ecode = make_response(
                jsonify(
                    {"status": args[2]},
                        {"data": {
                            "status": "success",
                            "message": "The connection was reset.",
                            "command": args[1]
                        }
                    }
                ), args[2])

        else:
            ecode = "Unrecognised error args[2]"

    return ecode