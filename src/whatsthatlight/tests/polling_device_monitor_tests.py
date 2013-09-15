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
from threading import Event

# Local imports
from whatsthatlight.common import logger
from whatsthatlight.common import packets
from whatsthatlight.common import parser
from whatsthatlight.device_monitors import PollingDeviceMonitor
from whatsthatlight.devices import PyUsbDevice, TeensyDevice, Blink1Device

# Third-party imports
from mockito import mock, when
from mockito import verify  # @UnusedImport


class Test(unittest.TestCase):

    def setUp(self):
        '''
        Setup.
        '''
        self._logger = logger.get_logger('src/whatsthatlight/logger.conf')
        self.__name__ = 'Test'

        # Use this line to run single test
        #self._logger = logger.get_logger('../logger.conf')

    def test_start_and_stop(self):
        '''
        Basic start and stop test.
        '''
        mock_device = mock()
        monitors = PollingDeviceMonitor(mock_device, logger=self._logger)
        monitors.start()
        self.assertTrue(monitors.running)
        monitors.stop()
        self.assertFalse(monitors.running)

    def test_start_and_start_again(self):
        '''
        Trying to start twice must not fail.
        '''
        mock_device = mock()
        monitors = PollingDeviceMonitor(mock_device, logger=self._logger)
        monitors.start()
        self.assertTrue(monitors.running)
        monitors.start()
        self.assertTrue(monitors.running)
        monitors.stop()
        self.assertFalse(monitors.running)

    def test_stop_and_stop_again(self):
        '''
        Trying to stop twice must not fail.
        '''
        mock_device = mock()
        monitors = PollingDeviceMonitor(mock_device, logger=self._logger)
        monitors.start()
        self.assertTrue(monitors.running)
        monitors.stop()
        self.assertFalse(monitors.running)
        monitors.stop()
        self.assertFalse(monitors.running)

    def test_add_remove_handlers_invoked_error_on_send(self):
        # Overriding the default log level so that the instructions are clear
        # and not obfuscated by the many debug messages.
        self._logger.setLevel('INFO')

        # Basics
        add_event = Event()
        remove_event = Event()
        polling_period = 0.1
        timeout = polling_period * 2
        iterations = 2

        def _add_event_handler():
            self._logger.info('Invoked')
            add_event.set()

        def _remove_event_handler():
            self._logger.info('Invoked')
            remove_event.set()

        # Set up the mock sequence
        #  A single iteration:
        #   is_open:False
        #   open
        #   (invoke add handler)
        #   is_open:True
        #   send:challenge request
        #   receive:challenge response
        #   is_open:True
        #   send:IOError
        #   close
        #   (invoke remove handler)
        #   is_open:False
        mock_device = mock()
        (when(mock_device).is_open().
            thenReturn(False).  # Iteration 1
            thenReturn(True).
            thenReturn(True).
            thenReturn(False).
            thenReturn(False).  # Iteration 2
            thenReturn(True).
            thenReturn(True).
            thenReturn(False))
        (when(mock_device).send(parser.get_challenge_request()).
            thenReturn(None).  # Iteration 1
            thenRaise(IOError).
            thenReturn(None).  # Iteration 2
            thenRaise(IOError))
        when(mock_device).receive().thenReturn(packets.CHALLENGE_RESPONSE)

        # Construct a monitor
        monitor = PollingDeviceMonitor(mock_device,
                                       polling_interval=polling_period,
                                       logger=self._logger)
        monitor.set_add_event_handler(_add_event_handler)
        monitor.set_remove_event_handler(_remove_event_handler)

        # Start
        add_event.clear()
        remove_event.clear()
        monitor.start()
        self.assertTrue(monitor.running)

        for i in range(0, iterations):
            # Wait for events to be raised
            self._logger.info('Iteration  {0} / {1}'.format(i + 1, iterations))
            self._logger.info('Waiting for device to be connected')
            add_event.wait(timeout)
            add_event.clear()
            self._logger.info('Waiting for device to be disconnected')
            remove_event.wait(timeout)
            remove_event.clear()

        # Stop
        monitor.stop()
        self.assertFalse(monitor.running)

    def test_add_remove_handlers_invoked_error_on_receive(self):
        # Overriding the default log level so that the instructions are clear
        # and not obfuscated by the many debug messages.
        self._logger.setLevel('INFO')

        # Basics
        add_event = Event()
        remove_event = Event()
        polling_period = 0.1
        timeout = polling_period * 2
        iterations = 2

        def _add_event_handler():
            self._logger.info('Invoked')
            add_event.set()

        def _remove_event_handler():
            self._logger.info('Invoked')
            remove_event.set()

        # Set up the mock sequence
        #  A single iteration:
        #   is_open:False
        #   open
        #   (invoke add handler)
        #   is_open:True
        #   send:challenge request
        #   receive:challenge response
        #   is_open:True
        #   send:challenge request
        #   receive:IOError
        #   close
        #   (invoke remove handler)
        #   is_open:False
        mock_device = mock()
        (when(mock_device).is_open().
            thenReturn(False).  # Iteration 1
            thenReturn(True).
            thenReturn(True).
            thenReturn(False).
            thenReturn(False).  # Iteration 2
            thenReturn(True).
            thenReturn(True).
            thenReturn(False))
        when(mock_device).send(parser.get_challenge_request())
        (when(mock_device).receive().
            thenReturn(packets.CHALLENGE_RESPONSE).  # Iteration 1
            thenRaise(IOError).
            thenReturn(packets.CHALLENGE_RESPONSE).  # Iteration 2
            thenRaise(IOError))

        # Construct a monitor
        monitor = PollingDeviceMonitor(mock_device,
                                       polling_interval=polling_period,
                                       logger=self._logger)
        monitor.set_add_event_handler(_add_event_handler)
        monitor.set_remove_event_handler(_remove_event_handler)

        # Start
        add_event.clear()
        remove_event.clear()
        monitor.start()
        self.assertTrue(monitor.running)

        for i in range(0, iterations):
            # Wait for events to be raised
            self._logger.info('Iteration  {0} / {1}'.format(i + 1, iterations))
            self._logger.info('Waiting for device to be connected')
            add_event.wait(timeout)
            add_event.clear()
            self._logger.info('Waiting for device to be disconnected')
            remove_event.wait(timeout)
            remove_event.clear()

        # Stop
        monitor.stop()
        self.assertFalse(monitor.running)

    def test_add_remove_handlers_invoked_error_on_open(self):
        # Overriding the default log level so that the instructions are clear
        # and not obfuscated by the many debug messages.
        self._logger.setLevel('INFO')

        # Basics
        add_event = Event()
        remove_event = Event()
        polling_period = 0.1
        timeout = polling_period * 2

        def _add_event_handler():
            self._logger.info('Invoked')
            add_event.set()

        def _remove_event_handler():
            self._logger.info('Invoked')
            remove_event.set()

        # Set up the mock sequence
        #   is_open:False
        #   open:IOError
        #   (MUST NOT invoke add handler)
        #   is_open:False
        #   open
        #   (invoke add handler)
        #   is_open:True
        #   send:challenge request
        #   receive:challenge response
        #   is_open:True
        #   send:IOError
        #   close
        #   (invoke remove handler)
        #   is_open:False

        mock_device = mock()
        (when(mock_device).open().
            thenRaise(IOError).
            thenReturn(None))
        (when(mock_device).is_open().
            thenReturn(False).
            thenReturn(False).
            thenReturn(True).
            thenReturn(True).
            thenReturn(False))
        (when(mock_device).send(parser.get_challenge_request()).
            thenReturn(None).
            thenRaise(IOError))
        when(mock_device).receive().thenReturn(packets.CHALLENGE_RESPONSE)

        # Construct a monitor
        monitor = PollingDeviceMonitor(mock_device,
                                       polling_interval=polling_period,
                                       logger=self._logger)
        monitor.set_add_event_handler(_add_event_handler)
        monitor.set_remove_event_handler(_remove_event_handler)

        # Start
        add_event.clear()
        remove_event.clear()
        monitor.start()
        self.assertTrue(monitor.running)

        # Wait for events to be raised
        self._logger.info('Waiting for device to be connected')
        add_event.wait(timeout)
        add_event.clear()
        self._logger.info('Waiting for device to be disconnected')
        remove_event.wait(timeout)
        remove_event.clear()

        # Stop
        monitor.stop()
        self.assertFalse(monitor.running)

    @unittest.skip
    def test_manually(self):
        # Overriding the default log level so that the instructions are clear
        # and not obfuscated by the many debug messages.
        self._logger.setLevel('INFO')

        # Pick a device class
        #device_class = 'pyusb'
        #device_class = 'teensy'
        device_class = 'blink1'

        # Other
        add_event = Event()
        remove_event = Event()
        timeout = 10
        iterations = 3

        def _add_event_handler():
            self._logger.info('Invoked')
            add_event.set()

        def _remove_event_handler():
            self._logger.info('Invoked')
            remove_event.set()

        # Construct a monitor
        if device_class == 'pyusb':
            device = PyUsbDevice(0x27b8,
                                 0x01ed,
                                 1)
        elif device_class == 'teensy':
            device = TeensyDevice(0x27b8,
                                  0x01ed,
                                  0xffc9,
                                  0x0004)
        elif device_class == 'blink1':
            device = Blink1Device(0x16c0,
                                  0x0486,
                                  0)
        else:
            raise Exception('Invalid or device class not supported')
        monitor = PollingDeviceMonitor(device,
                                       polling_interval=1,
                                       logger=self._logger)
        monitor.set_add_event_handler(_add_event_handler)
        monitor.set_remove_event_handler(_remove_event_handler)

        # Start
        add_event.clear()
        remove_event.clear()
        monitor.start()
        self.assertTrue(monitor.running)

        for i in range(0, iterations):
            # Wait for events to be raised
            self._logger.info('Iteration  {0} / {1}'.format(i + 1, iterations))
            self._logger.info('Waiting for device to be connected')
            add_event.wait(timeout)
            add_event.clear()
            self._logger.info('Waiting for device to be disconnected')
            remove_event.wait(timeout)
            remove_event.clear()

        # Stop
        monitor.stop()
        self.assertFalse(monitor.running)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_foo']
    unittest.main()
