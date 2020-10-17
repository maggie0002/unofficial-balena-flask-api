# unofficial-balena-flask-api

This is a web interface to allow a browser to trigger a series of actions on Balena OS devices. 

This is not provided as a thoroughly tested container ready for production, but as example approaches for input and further development. 

Current features include ability to:

- Check the connection status of the wifi
- Launch wifi-connect when network not available
- Disconnect wifi-connect and clear the saved connection
- Change the device hostname
- Amend the wifi-connect SSID to include the last two digits of new hostnames in order to distinguish devices
- Retrive journald logs to your browser
- Update the device containers from your Open Balena or Balena cloud instance

By default, available on http://yourdeviceiporhostname:9090/v1/
    connectionstatus
    hostconfig/<yournewhostname>
    journallogs
    update
    wifireset
