#Copyright 2013 Pieter Rautenbach
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# System imports
import logging
import threading
from time import sleep

# Constants
_VENDOR_ID_KEY = 'ID_VENDOR_ID'
_PRODUCT_ID_KEY = 'ID_MODEL_ID'
_ACTION_KEY = 'ACTION'
_ADD_ACTION = 'add'
_REMOVE_ACTION = 'remove'


class BaseDeviceMonitor(object):
    '''
    Base class for constructing different device monitors.
    '''

    def __init__(self,
                 logger=logging.basicConfig()):
        '''
        Base constructor.
        :param logger: local logger instance
        '''
        self._logger = logger
        self.event_handlers = {'add': None,
                               'remove': None}
        self.running = False
        self._runLock = threading.Lock()

    def _get_add_event_handler(self):
        '''
        The method for handling the event when a device was added.
        '''
        return self.event_handlers[_ADD_ACTION]

    def set_add_event_handler(self, handler):
        '''
        Set a method for handling the event when a device was added.
        :param handler: A parameterless void method.
        '''
        self._logger.debug('Setting a new add event handler: {0}'.
                           format(handler))
        self.event_handlers[_ADD_ACTION] = handler

    def _get_remove_event_handler(self):
        '''
        The method for handling the event when a device was removed.
        '''
        return self.event_handlers[_REMOVE_ACTION]

    def set_remove_event_handler(self, handler):
        '''
        Set a method for handling the event when a device was removed.
        :param handler: A parameterless void method.
        '''
        self._logger.debug('Setting a new add event handler: {0}'.
                           format(handler))
        self.event_handlers[_REMOVE_ACTION] = handler


class PyUdevDeviceMonitor(BaseDeviceMonitor):
    '''
    A wrapper class for pyudev for detecting when a specific USB device is
    connected or disconnected.
    '''

    def __init__(self,
                 vendor_id,
                 product_id,
                 udev_module,
                 logger=logging.basicConfig()):
        '''
        Constructor.
        :param vendor_id: the USB device's vendor ID
        :param product_id: the USB device's product ID
        :param callback: the method to evoke when the monitored device changed
        :param logger: local logger instance
        '''
        super(type(self), self).__init__(logger=logger)
        # pyudev provide the values as hex strings, without the 0x prefix
        # and exactly 4 digits, e.g. 0xa12b becomes a12b
        self._vendor_id = vendor_id
        self._product_id = product_id

        # Event callback handler as a closure
        def _device_event_handler(device):
            vendor_id = int(device[_VENDOR_ID_KEY], 16)
            product_id = int(device[_PRODUCT_ID_KEY], 16)
            self._logger.debug('Device event handler invoked for '
                               'vid_%0#6x, pid_%0#6x',
                               vendor_id, product_id)
            if (not vendor_id == self._vendor_id or
                not product_id == self._product_id):
                    self._logger.debug('Device does not match the \
                                        required VID and PID \
                                        (vid_%0#6x, pid_%0#6x)',
                                       self._vendor_id,
                                       self._product_id)
                    return
            add_event_handler = self._get_add_event_handler()
            remove_event_handler = self._get_remove_event_handler()
            if (device[_ACTION_KEY] == _ADD_ACTION and
                not add_event_handler is None):
                    add_event_handler()
            elif (device[_ACTION_KEY] == _REMOVE_ACTION and
                  not remove_event_handler is None):
                    remove_event_handler()
            else:
                self._logger.debug('Unknown device event or no handler')

        context = udev_module.Context()
        monitor = udev_module.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='usb', device_type='usb_device')

        # Note that the observer runs by default as a daemon thread
        self._observer = (udev_module.
                          MonitorObserver(monitor,
                                          callback=_device_event_handler,
                                          name='device_observer'))

    def start(self):
        '''
        Start the device monitor.
        '''
        self._logger.info("Device monitor starting")
        with self._runLock:
            if self.running:
                self._logger.warn("Device monitor already started")
                return
            self.running = True
            self._observer.start()
            self._logger.info("Device monitor started")

    def stop(self):
        '''
        Stop the device monitor.
        '''
        self._logger.info("Device monitor stopping")
        with self._runLock:
            if not self.running:
                self._logger.warn("Device monitor already stopped")
                return

            # CONSIDER: Test is_alive before stopping observer
            self._observer.stop()
            self.running = False
            self._logger.info("Device monitor stopped")


class PollingDeviceMonitor(BaseDeviceMonitor):
    '''
    A polling device monitor when no event-driven support is available.
    '''

    def __init__(self,
                 device,
                 polling_interval=1,
                 logger=logging.basicConfig()):
        '''
        Constructor.
        :param device: a device
        :param polling_interval: the polling period in seconds
        :param logger: local logger instance
        '''
        super(type(self), self).__init__(logger=logger)
        self._polling_interval = polling_interval
        self._device = device
        self._thread = threading.Thread(target=self._run)

    def start(self):
        '''
        Start the device monitor.
        '''
        self._logger.info("Device monitor starting")
        with self._runLock:
            if self.running:
                self._logger.warn("Device monitor already started")
                return
            self.running = True
            self._thread.start()
            self._logger.info("Device monitor started")

    def stop(self):
        '''
        Stop the device monitor.
        '''
        self._logger.info("Device monitor stopping")
        with self._runLock:
            if not self.running:
                self._logger.warn("Device monitor already stopped")
                return

            self.running = False
            self._thread.join()
            self._logger.info("Device monitor stopped")

    def _run(self):
        '''
        Polling thread.
        '''
        while self.running:
            # Transition from open to close (removed)
            if self._device.is_open():
                try:
                    self._logger.debug('Device open - polling')
                    if not self._device.poll():
                        self._device.close()
                        self._get_remove_event_handler()()
                except IOError:
                    self._device.close()
                    self._get_remove_event_handler()()
            # Transition from close to open (added)
            else:
                try:
                    self._logger.debug('Trying to open device')
                    self._device.open()
                    if not self._get_add_event_handler() is None:
                        self._get_add_event_handler()()
                except IOError:
                    pass
            self._logger.debug('Sleeping for {0} second(s)'.
                               format(self._polling_interval))
            sleep(self._polling_interval)
