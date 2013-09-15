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
import importlib

# Local imports
from common import parser
from common import utils


class DeviceError(Exception):
    '''
    Generic device exception.
    '''

    def __init__(self, message):
        '''
        Constructor.
        :param message: the message explaining the exception
        '''
        self.message = message


class TeensyDevice(object):
    '''
    Wrapper class for a Teensy device using the TeensyRawhid module. This
    also serves as an interface for using any other module to communicate
    with a USB device.
    '''

    def __init__(self,
                 vendor_id,
                 product_id,
                 usage_page,
                 usage):
        '''
        Constructor.
        :param vendor_id: the device's VID
        :param product_id: the device's PID
        :param usage_page: the device's usage page
        :param usage: the device's usage
        '''
        self._packet_size = 64
        self._timeout = 50
        self._vendor_id = vendor_id
        self._product_id = product_id
        self._usage_page = usage_page
        self._usage = usage
        self._device = importlib.import_module('TeensyRawhid').Rawhid()

    def get_vendor_id(self):
        '''
        Get the vendor ID of the device.
        '''
        return self._vendor_id

    def get_product_id(self):
        '''
        Get the product ID of the device.
        '''
        return self._product_id

    def get_packet_size(self):
        '''
        Get the size for sending data.
        '''
        return self._packet_size

    def open(self):
        '''
        Open the device for communication.
        '''
        self._device.open(self._vendor_id,
                          self._product_id,
                          self._usage_page,
                          self._usage)

    def is_open(self):
        '''
        Check whether the device is open for communication.
        '''
        return self._device.isOpened()

    def send(self, data):
        '''
        Send raw data.
        :param data: the binary data
        '''
        self._device.send(data, self._timeout)

    def receive(self):
        '''
        Receive binary data.
        '''
        return self._device.recv(self._packet_size, self._timeout)

    def poll(self):
        '''
        Poll the device.
        '''
        self._device.send(parser.get_challenge_request())
        r = self._device.receive()
        self._logger.debug('\'{0}\''.format(utils.strip(r)))
        assert(parser.is_challenge_response(r))

    def close(self):
        '''
        Close the device for communication.
        '''
        self._device.close()


class PyUsbDevice(object):
    '''
    Wrapper class for a PyUSB device using the PyUSB module.
    '''

    def __init__(self,
                 vendor_id,
                 product_id,
                 interface_number):
        '''
        Constructor.
        :param vendor_id: the device's VID
        :param product_id: the device's PID
        :param interface_number: the device's interface number to use
        '''
        self._vendor_id = vendor_id
        self._product_id = product_id
        self._interface_number = interface_number
        self._clear()
        self._pyusb = importlib.import_module('usb')

    def get_vendor_id(self):
        '''
        Get the vendor ID of the device.
        '''
        return self._vendor_id

    def get_product_id(self):
        '''
        Get the product ID of the device.
        '''
        return self._product_id

    def get_packet_size(self):
        '''
        Get the size for sending data.
        '''
        if not self.is_open():
            raise DeviceError('Packet size only available if \
                               the device is connected')
        return self._bulk_in_endpoint.wMaxPacketSize

    def open(self):
        '''
        Open the device for communication.
        '''
        self._clear()
        device = self._pyusb.core.find(idVendor=self.get_vendor_id(),
                                       idProduct=self.get_product_id())
        if device is None:
            raise IOError('Device could not be found')
        self._device = device
        configuration = self._device[0]
        interface = configuration[(self._interface_number, 0)]
        self._bulk_in_endpoint = interface[0]
        self._bulk_out_endpoint = interface[1]
        try:
            self._device.detach_kernel_driver(self._interface_number)
            self._device.set_configuration()
        except:
            pass

    def is_open(self):
        '''
        Check whether the device is open for communication.
        '''
        return (not self._device is None and
                not self._bulk_in_endpoint is None and
                not self._bulk_out_endpoint is None)

    def send(self, data):
        '''
        Send raw data.
        :param data: the binary data
        '''
        if not self.is_open():
            raise DeviceError('The device is not open')
        number_of_bytes = self._bulk_out_endpoint.write(data)
        if not number_of_bytes == len(data):
            raise IOError('There was a problem sending the data: \
                           written {0} bytes, but expected {1} bytes '.
                          format(number_of_bytes, len(data)))

    def receive(self):
        '''
        Receive raw data.
        '''
        if not self.is_open():
            raise DeviceError('The device is not open')
        data = self._bulk_in_endpoint.read(self.get_packet_size())
        if not len(data) == self._bulk_in_endpoint.wMaxPacketSize:
            raise IOError('There was a problem reading the data: \
                           read {0} bytes, but expected {1} bytes'.
                          format(len(data),
                                 self._bulk_in_endpoint.wMaxPacketSize))
        return data.tostring()

    def poll(self):
        '''
        Poll the device.
        '''
        self._device.send(parser.get_challenge_request())
        r = self._device.receive()
        self._logger.debug('\'{0}\''.format(utils.strip(r)))
        assert(parser.is_challenge_response(r))

    def _clear(self):
        '''
        Clear the different handlers
        '''
        self._device = None
        self._bulk_in_endpoint = None
        self._bulk_out_endpoint = None

    def close(self):
        '''
        Close the device for communication.
        '''
        self._clear()


class HidApiDevice(object):
    '''
    Wrapper class for an HID device using the Cython HID API module.
    '''

    def __init__(self,
                 vendor_id,
                 product_id,
                 usage_page,
                 usage):
        '''
        Constructor.
        :param vendor_id: the device's VID
        :param product_id: the device's PID
        :param usage_page: the device's usage page
        :param usage: the device's usage
        '''
        self._packet_size = 64
        self._timeout = 50
        self._vendor_id = vendor_id
        self._product_id = product_id
        self._usage_page = usage_page
        self._usage = usage
        self._device = importlib.import_module('hid')

    def get_vendor_id(self):
        '''
        Get the vendor ID of the device.
        '''
        return self._vendor_id

    def get_product_id(self):
        '''
        Get the product ID of the device.
        '''
        return self._product_id

    def get_packet_size(self):
        '''
        Get the size for sending data.
        '''
        return self._packet_size

    def open(self):
        '''
        Open the device for communication.
        '''
        self._device.open(self._vendor_id,
                          self._product_id,
                          self._usage_page,
                          self._usage)

    def is_open(self):
        '''
        Check whether the device is open for communication.
        '''
        return self._device.isOpened()

    def send(self, data):
        '''
        Send raw data.
        :param data: the binary data
        '''
        self._device.send(data, self._timeout)

    def receive(self):
        '''
        Receive binary data.
        '''
        return self._device.recv(self._packet_size, self._timeout)

    def poll(self):
        '''
        Poll the device.
        '''
        self._device.send(parser.get_challenge_request())
        r = self._device.receive()
        self._logger.debug('\'{0}\''.format(utils.strip(r)))
        assert(parser.is_challenge_response(r))

    def close(self):
        '''
        Close the device for communication.
        '''
        self._device.close()


class Blink1Device(object):
    '''
    Wrapper class for a blink(1) device using PyUSB
    Code taken from:
    https://getsatisfaction.com/thingm/topics/more_comprehensive_python_support
    '''

    def __init__(self,
                 vendor_id,
                 product_id,
                 interface_number):
        '''
        Constructor.
        :param vendor_id: the device's VID
        :param product_id: the device's PID
        :param interface_number: the device's interface number to use
        '''
        self._vendor_id = vendor_id
        self._product_id = product_id
        self._interface_number = interface_number
        self._clear()
        self._pyusb = importlib.import_module('usb')

    def get_vendor_id(self):
        '''
        Get the vendor ID of the device.
        '''
        return self._vendor_id

    def get_product_id(self):
        '''
        Get the product ID of the device.
        '''
        return self._product_id

    def get_packet_size(self):
        '''
        Get the size for sending data.
        '''
        if not self.is_open():
            raise DeviceError('Packet size only available if \
                               the device is connected')
        return self._bulk_in_endpoint.wMaxPacketSize

    def open(self):
        '''
        Open the device for communication.
        '''
        self._clear()
        device = self._pyusb.core.find(idVendor=self.get_vendor_id(),
                                       idProduct=self.get_product_id())
        if device is None:
            raise IOError('Device could not be found')
        self._device = device
        try:
            self._device.detach_kernel_driver(self._interface_number)
            self._device.set_configuration()
        except:
            pass

    def is_open(self):
        '''
        Check whether the device is open for communication.
        '''
        return (not self._device is None)

    def send(self, data):
        '''
        Send raw data.
        :param data: the binary data
        '''
        if data == None:
            return
        if not self.is_open():
            raise DeviceError('The device is not open')
        bm_request_type_out = self._pyusb.util.build_request_type(
                                    self._pyusb.util.CTRL_OUT,
                                    self._pyusb.util.CTRL_TYPE_CLASS,
                                    self._pyusb.util.CTRL_RECIPIENT_INTERFACE)
        number_of_bytes = self._device.ctrl_transfer(bm_request_type_out,
                                                     0x09,
                                                     (3 << 8) | 0x01,
                                                     0,
                                                     data)
        if not number_of_bytes == len(data):
            raise IOError('There was a problem sending the data: \
                           written {0} bytes, but expected {1} bytes '.
                          format(number_of_bytes, len(data)))

    def receive(self):
        '''
        Receive raw data.
        '''
        if not self.is_open():
            raise DeviceError('The device is not open')
        bm_request_type_in = self._pyusb.util.build_request_type(
                                    self._pyusb.util.CTRL_IN,
                                    self._pyusb.util.CTRL_TYPE_CLASS,
                                    self._pyusb.util.CTRL_RECIPIENT_INTERFACE)
        data = self._device.ctrl_transfer(bm_request_type_in,
                                          0x01,
                                          (3 << 8) | 0x01,
                                          0,
                                          8)
        return data

    def poll(self):
        '''
        Poll the device.
        '''
        # 0x76 = 'v' => get version
        self.send([0x00, 0x76, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        assert self.receive()
        return True

    def _clear(self):
        '''
        Clear the different handlers
        '''
        self._device = None
        self._bulk_in_endpoint = None
        self._bulk_out_endpoint = None

    def close(self):
        '''
        Close the device for communication.
        '''
        self._clear()
