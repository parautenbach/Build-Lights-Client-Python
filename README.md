Build Lights Client (Python)
============================

A Python build lights client that can receive build notifications from a notification server connected to a build server.

# Installation 
This details the steps for a Debian-based system, but it should be fairly easy to figure out the steps for a RedHat-based distro.
## Dependencies
* Eclipse (Indigo or newer)
* Python 2.7 or newer
* `sudo apt-get install python-dev`
* `sudo apt-get install libudev-dev`
* `sudo apt-get install libusb-dev`
* `sudo apt-get install python-pip` (or `sudo easy_install pip`)
* `sudo apt-get install python-pyudev` (or `sudo pip install pyudev`)
* [Download pyusb](http://sourceforge.net/projects/pyusb/)
 * unzip and enter unzipped directory
 * `sudo python setup.py install`

## Client
* Export this repo to `/usr/local/notifier_client`
* `sudo cp /usr/local/notifier_client/51-blink1.rules /etc/udev/rules.d/`
* `sudo chmod 755 /usr/local/notifier_client/src/whatsthatlight/notifier_client_console.py`
* `sudo vi /usr/local/notifier_client/src/whatsthatlight/notifier_client.conf`
* Under the `[client]` section:
 * Change username to your build server username (not your SVN or Git username)
 * Change address to your public IP (do not use `0.0.0.0` as the IP is sent to the server for registration)
* The pedantic ones can also copy `notifier_client.conf` to `/etc/`. If so, edit `notifier_client_daemon.conf` (below) so that the script can find this config file during start-up.
* `sudo vi /usr/local/notifier_client/src/whatsthatlight/logger.conf`
* Under `[handler_rotatingFileHandler]` set `args=('/var/log/notifier_client.log',)`
* `sudo cp /usr/local/notifier_client/src/whatsthatlight/notifier_client_daemon.conf /etc/init/`
* `sudo initctl reload-configuration`
* `sudo start notifier_client_daemon`
* `sudo tail -f /usr/local/notifier_client/src/whatsthatlight/notifier_client.log`

## Mac OS X
Note: This is only a brief guidline until I've had time to test all of this properly.
* Install the dependencies as for the Linux client, with the following exceptions:
 * There's no (direct) IOKit support in python, so don't install any of the udev packages. Instead, select the polling device monitor in `notifier_client.conf`.
 * `libusb` has to be installed using homebrew (or macports).
* Install the software to `/Library/LaunchDaemons/notifier_client/`.
* OS X does not use upstart for daemons, but LaunchDaemon. You need to create a `/Library/LaunchDaemons/notifier_client/notifier_client.plist` file, reload it with `launchctl` and start it with `launchd`.
