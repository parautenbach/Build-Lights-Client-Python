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
import binascii

# Local imports
from common import utils
from common import usb_transfer_types

# Constants
_ACK = 'ack'
_TIMEOUT = 50
_VENDOR_ID_KEY = 'ID_VENDOR_ID'
_PRODUCT_ID_KEY = 'ID_MODEL_ID'


class DeviceController(object):
    '''
    Build lights USB device controller.
    '''

    def __init__(self,
                 device,
                 usb_transfer_type,
                 monitor,
                 add_event_handler=None,
                 remove_event_handler=None,
                 logger=logging.basicConfig()):
        '''
        Constructor.
        :param device: any module that defines the same interface as the
                       TeensyRawhid module's Rawhid class
        :param usb_transfer_type: How data gets transferred (raw or control)
        :param monitor: a device monitor, implementing the PyUdevDeviceMonitor
                        interface
        :param add_event_handler: void, parameterless method to invoke when a
                                  device connected
        :param remove_event_handler: void, parameterless method to invoke when
                                     a device disconnected
        :param logger: local logger instance
        '''
        self._logger = logger
        self.running = False
        self._runLock = threading.Lock()
        self._device = device
        self._usb_transfer_type = usb_transfer_type
        self.event_handlers = {'add': None,
                               'remove': None}
        self.set_add_event_handler(add_event_handler)
        self.set_remove_event_handler(remove_event_handler)

        def _add_event_handler():
            self._device.open()
            add_event_handler = self._get_add_event_handler()
            if not add_event_handler is None:
                add_event_handler()

        def _remove_event_handler():
            self._device.close()
            remove_event_handler = self._get_remove_event_handler()
            if not remove_event_handler is None:
                remove_event_handler()

        self._monitor = monitor
        self._monitor.set_add_event_handler(_add_event_handler)
        self._monitor.set_remove_event_handler(_remove_event_handler)

    def start(self):
        '''
        Start the device controller.
        '''
        self._logger.info("Device controller starting")
        with self._runLock:
            if self.running:
                self._logger.warn("Device controller already started")
                return
            self._open_device()
            if (self._device_is_open() and
                not self._get_add_event_handler() is None):
                self._get_add_event_handler()()
            self.running = True
            self._monitor.start()
            self._logger.info("Device controller started")

    def stop(self):
        '''
        Stop the device controller.
        '''
        self._logger.info("Device controller stopping")
        with self._runLock:
            if not self.running:
                self._logger.warn("Device controller already stopped")
                return

            # CONSIDER: Test is_alive before stopping observer
            self._monitor.stop()
            self._close_device()
            self.running = False
            self._logger.info("Device controller stopped")

    def _get_add_event_handler(self):
        '''
        The method for handling the event when a device was added.
        '''
        return self.event_handlers['add']

    def set_add_event_handler(self, handler):
        '''
        Set a method for handling the event when a device was added.
        :param handler: A parameterless void method.
        '''
        self._logger.debug('Setting a new add event handler: {0}'.
                           format(handler))
        self.event_handlers['add'] = handler

    def _get_remove_event_handler(self):
        '''
        Get the method for handling the event when a device was removed.
        '''
        return self.event_handlers['remove']

    def set_remove_event_handler(self, handler):
        '''
        Set a method for handling the event when a device was removed.
        :param handler: A parameterless void method.
        '''
        self._logger.debug('Setting a new remove event handler: {0}'.
                           format(handler))
        self.event_handlers['remove'] = handler

    def _device_is_open(self):
        '''
        Checks whether the device is open for communication.
        '''
        return self._device.is_open()

    def _open_device(self):
        '''
        Open the device for communication.
        '''
        # Time for a rant: If you specify both the alternate
        # form (#) and padding, you have to include the 0x in
        # the field width specifier (i.e. 4 digits become 6).
        # I guess it makes sense, but at first it really was
        # counter intuitive.
        self._logger.info('Trying to open device (vid_%0#6x, pid_%0#6x)',
                          self._device.get_vendor_id(),
                          self._device.get_product_id())
        try:
            self._device.open()
        except IOError, e:
            self._logger.debug(e)

    def _close_device(self):
        '''
        Close the device if it is open.
        '''
        self._logger.info('Closing device')
        if self._device_is_open():
            self._device.close()

    def send(self, command):
        '''
        Send a command (report) to the USB device. The method returns True if
        the command was sent and understood.
        :param command: A command in the format <key>=<value><newline>, e.g.
                        'red=on\n'.
        '''
        if self._usb_transfer_type == usb_transfer_types.RAW:
            if not self._device_is_open():
                return False
            data = command + '\0' * (self._device.get_packet_size() -
                                     len(command))
            self._logger.debug('Sending data (%u bytes): %s',
                               len(data),
                               binascii.b2a_hex(data))
            try:
                self._device.send(data)
                data = self._device.receive()
                self._logger.debug('Received data (%u bytes): %s',
                                   len(data),
                                   binascii.b2a_hex(data))
                return utils.strip(data) == _ACK
            except IOError:
                return False
        elif self._usb_transfer_type == usb_transfer_types.CONTROL:
            self._device.send(command)
