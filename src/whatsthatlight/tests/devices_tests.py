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
import unittest

# Local imports
from whatsthatlight.devices import PyUsbDevice, TeensyDevice, DeviceError
from whatsthatlight.common import logger


class Test(unittest.TestCase):

    def setUp(self):
        '''
        Setup.
        '''
        self._logger = logger.get_logger('src/whatsthatlight/logger.conf')
        self.__name__ = 'Test'

        # Use this line to run single test
        #self._logger = logger.get_logger('../logger.conf')

    def test_teensy_device_get_vendor_and_product_ids(self):
        '''
        Test that the VID and PID supplied with the constructor is returned.
        '''
        vendor_id = 0xa1b2
        product_id = 0xc3d4
        usage_page = 0xe5f6
        usage = 0x1ab2
        device = TeensyDevice(vendor_id,
                              product_id,
                              usage_page,
                              usage)
        self.assertEqual(device.get_vendor_id(), vendor_id)
        self.assertEqual(device.get_product_id(), product_id)

    def test_pyusb_device_get_vendor_and_product_ids(self):
        '''
        Test that the VID and PID supplied with the constructor is returned.
        '''
        vendor_id = 0xe5f6
        product_id = 0x1ab2
        interface_number = 0
        device = PyUsbDevice(vendor_id,
                             product_id,
                             interface_number)
        self.assertEqual(device.get_vendor_id(), vendor_id)
        self.assertEqual(device.get_product_id(), product_id)

    def test_teensy_device_get_packet_size_must_never_fail(self):
        '''
        The Teensy's packet size is preset and must be available and non-zero
        even if the device is not connected.
        '''
        vendor_id = 0
        product_id = 0
        usage_page = 0
        usage = 0
        device = TeensyDevice(vendor_id,
                              product_id,
                              usage_page,
                              usage)
        self.assertGreater(device.get_packet_size(), 0)

    def test_pyusb_device_get_packet_size_unavailable_if_closed(self):
        '''
        PyUSB's packet size is only available when the device is connected.
        '''
        vendor_id = 0
        product_id = 0
        interface_number = 0
        device = PyUsbDevice(vendor_id,
                             product_id,
                             interface_number)
        self.assertFalse(device.is_open())
        self.assertRaises(DeviceError, device.get_packet_size)

    def test_teensy_device_no_such_device(self):
        '''
        Operations must fail if there's no such device.
        '''
        # So it seems TeensyRawhid will actually sometimes not raise an IOError
        # for an invalid VID and PID (i.e. it will return None as if it has
        # successfully opened the device). This is awkward and probably a
        # bug -- either in TeensyRawhid or in the kernel. Replicate this by
        # executing open(...) consecutively on an interactive Python terminal:
        # The first invocation will fail and the subsequent ones succeed. If
        # you then wait a while (a few minutes, but I don know exactly how
        # long) and try again it will again fail, before succeeding again. What
        # does seem to make a difference is to use values greater than zero. It
        # will then behave consistently.
        vendor_id = 0x1
        product_id = 0x1
        usage_page = 0x1
        usage = 0x1
        device = TeensyDevice(vendor_id,
                              product_id,
                              usage_page,
                              usage)
        self.assertRaises(IOError, device.open)
        self.assertFalse(device.is_open())
        self.assertRaises(IOError, device.send, 'foo')
        self.assertRaises(IOError, device.receive)

    def test_pyusb_device_no_such_device(self):
        '''
        Operations must fail if there's no such device.
        '''
        vendor_id = 0
        product_id = 0
        interface_number = 0
        device = PyUsbDevice(vendor_id,
                             product_id,
                             interface_number)
        self.assertRaises(IOError, device.open)
        self.assertFalse(device.is_open())
        self.assertRaises(DeviceError, device.send, 'foo')
        self.assertRaises(DeviceError, device.receive)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
