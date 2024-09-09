# Pricecutter

This is a small python app to control home automation system to shut down heating or heatpump compressor when electricity price is at highest.

This application uses external service to provide the control on when
to turn power on/off and for listing the current and next prices. The
application is integrated with https://porssari.fi for control and
for https://spot-hinta.fi for price information.

The application uses a relay control via Pimoroni Automation Hat on a
Raspberry Pi. The application displays the current status in the
Automation Hat embedded display and provides a web server which shows
the current status and next events.

Alternative to this controller is to use for example Shelly relay with
https://porssari.fi service.

## Configuration
            
The configuration of the application is done by setting up:

- The Raspberry Pi WiFi to access the house WiFi network. This can be
  done by starting the Raspberry Pi Zero and connecting it to display
  and keyboard and using `raspi-config` and selecting the Network
  Options/WiFI/WiFi Name and WiFi Password.
    
- The Mac address of the device used for authenticating to porssari.fi
  can be configured to config.py file as also the relay name.
    
- The service starts automatically at boot if crontab entry as
  following is added:
  `@reboot sleep 60 && cd pricecutter && nohup ./startup.sh 2>&1 > startup.log`

## Files

Following files are needed for the app:

- config.py -- the configuration of the device
- pricecutter.py -- the main app
- pricecutter_httpserver.py -- the web server for the app
- porssari.py -- the porssari.fi client

Additional files needed for development:
- automationhat.py -- mock version for automationhat dependency
- st7735.py -- mock version for st77535 display dependency
