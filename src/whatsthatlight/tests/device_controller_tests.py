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
from threading import Event, Thread
from time import sleep

# Local imports
import whatsthatlight.devices
import mock_pyudev
from whatsthatlight.device_controller import DeviceController
from whatsthatlight.device_monitors import PyUdevDeviceMonitor
from whatsthatlight.common import logger
from whatsthatlight.common import usb_transfer_types
from mock_device_monitor import MockDeviceMonitor

# Third-party imports
import pyudev
from mockito import mock, when
# PyDev bug (I think) causes incorrect warnings
# or mockito uses some bad practices...
from mockito import verify, any  # @UnusedImport
from mockito import inorder  # @UnresolvedImport


class Test(unittest.TestCase):
    '''
    Device controller tests.
    '''

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
        mock_monitor = mock()
        mock_device = mock()
        when(mock_device).get_vendor_id().thenReturn(0)
        when(mock_device).get_product_id().thenReturn(0)
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      logger=self._logger)
        controller.start()
        self.assertTrue(controller.running)
        controller.stop()
        self.assertFalse(controller.running)

    def test_start_and_start_again(self):
        '''
        Trying to start twice must not fail.
        '''
        mock_monitor = mock()
        mock_device = mock()
        when(mock_device).get_vendor_id().thenReturn(0)
        when(mock_device).get_product_id().thenReturn(0)
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      logger=self._logger)
        controller.start()
        self.assertTrue(controller.running)
        controller.start()
        self.assertTrue(controller.running)
        controller.stop()
        self.assertFalse(controller.running)

    def test_stop_and_stop_again(self):
        '''
        Trying to stop twice must not fail.
        '''
        mock_device = mock()
        when(mock_device).get_vendor_id().thenReturn(0)
        when(mock_device).get_product_id().thenReturn(0)
        when(mock_device).is_opened().thenReturn(True)
        mock_monitor = mock()
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      logger=self._logger)
        controller.start()
        self.assertTrue(controller.running)
        controller.stop()
        self.assertFalse(controller.running)
        controller.stop()
        self.assertFalse(controller.running)

    def test_start_with_device_connected(self):
        '''
        Test that the add event gets invoked on start-up.
        '''
        event = Event()
        event.clear()

        def _add_handler():
            self._logger.debug('Invoked')
            event.set()

        # Setup
        mock_monitor = mock()
        mock_device = mock()
        when(mock_device).get_vendor_id().thenReturn(0)
        when(mock_device).get_product_id().thenReturn(0)
        when(mock_device).is_open().thenReturn(True)
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      add_event_handler=_add_handler,
                                      logger=self._logger)

        # Execute
        controller.start()
        self.assertTrue(controller.running)
        event.wait()
        controller.stop()
        self.assertFalse(controller.running)

        # Verify mocks
        inorder.verify(mock_device, times=1).get_vendor_id()
        inorder.verify(mock_device, times=1).get_product_id()
        inorder.verify(mock_device, times=1).open()
        # Once on start-up and once on shutdown
        # But, it seems mockito needs it to be verified twice, otherwise
        # the verify.close will fail.
        inorder.verify(mock_device, times=2).is_open()
        inorder.verify(mock_device, times=2).is_open()
        inorder.verify(mock_device).close()

    def test_start_with_device_disconnected(self):
        '''
        Test that the add event does not get invoked on start-up.
        '''
        event = Event()
        event.clear()

        def _add_handler():
            self._logger.debug('Invoked')
            event.set()

        mock_monitor = MockDeviceMonitor(dormant=True)
        mock_device = mock()
        when(mock_device).get_vendor_id().thenReturn(0)
        when(mock_device).get_product_id().thenReturn(0)
        when(mock_device).is_open().thenReturn(False)

        # Execute
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      add_event_handler=_add_handler,
                                      logger=self._logger)
        controller.start()
        self.assertTrue(controller.running)
        event.wait(0.1)
        controller.stop()
        self.assertFalse(controller.running)

        # The event must not have been raised
        self.assertFalse(event.is_set(), 'Add handler must not be invoked')

        # Verify mocks
        inorder.verify(mock_device, times=1).get_vendor_id()
        inorder.verify(mock_device, times=1).get_product_id()
        inorder.verify(mock_device, times=1).open()
        # Once on start-up and once on shutdown
        # But, it seems mockito needs it to be verified twice, otherwise
        # the verify.close will fail.
        inorder.verify(mock_device, times=2).is_open()
        inorder.verify(mock_device, times=2).is_open()
        inorder.verify(mock_device, times=0).close()

    def test_add_remove_handler_must_not_be_invoked(self):
        '''
        Test that the add and remove handlers does NOT be invoked.
        '''
        # Execution controllers
        add_event = Event()
        remove_event = Event()
        add_event.clear()
        remove_event.clear()

        # Event handlers
        def _add_handler():
            self._logger.debug('Invoked')
            add_event.set()

        def _remove_handler():
            self._logger.debug('Invoked')
            remove_event.set()

        mock_device = mock()
        when(mock_device).get_vendor_id().thenReturn(0)
        when(mock_device).get_product_id().thenReturn(0)
        when(mock_device).is_open().thenReturn(False)

        # pyudev provide the values as hex strings, without the 0x prefix
        mock_pyudev.vendor_id = '0a1b'
        mock_pyudev.model_id = '2c3d'
        mock_pyudev.dormant = False
        mock_pyudev.delay = 0.1

        # This VID and PID must differ from the above
        mock_monitor = PyUdevDeviceMonitor(0,
                                           0,
                                           udev_module=mock_pyudev,
                                           logger=self._logger)

        wait_delay = mock_pyudev.delay * 2
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      add_event_handler=_add_handler,
                                      remove_event_handler=_remove_handler,
                                      logger=self._logger)
        controller.start()
        self.assertTrue(controller.running)

        # Wait for the handlers to be invoked
        add_event.wait(wait_delay)
        remove_event.wait(wait_delay)

        # Shut down
        controller.stop()
        self.assertFalse(controller.running)

        # Test after stopping so that we don't hang the test if an
        # assertion failed
        self.assertFalse(add_event.is_set(),
                         'Add handler must not be invoked')
        self.assertFalse(remove_event.is_set(),
                         'Rremove handler must not be invoked')
        verify(mock_device, times=1).open()
        verify(mock_device, times=2).is_open()

    def test_add_remove_handler_must_be_invoked(self):
        '''
        Test that the add and remove handlers get invoked.
        '''
        # Basics
        vendor_id_str = '0a1b'
        vendor_id = int(vendor_id_str, 16)
        product_id_str = '2c3d'
        product_id = int(product_id_str, 16)

        # Execution controllers
        add_event = Event()
        remove_event = Event()
        add_event.clear()
        remove_event.clear()

        # Event handlers
        def _add_handler():
            self._logger.debug('Invoked')
            add_event.set()

        def _remove_handler():
            self._logger.debug('Invoked')
            remove_event.set()

        mock_device = mock()
        when(mock_device).get_vendor_id().thenReturn(vendor_id)
        when(mock_device).get_product_id().thenReturn(product_id)

        # pyudev provide the values as hex strings, without the 0x prefix
        mock_pyudev.vendor_id = vendor_id_str
        mock_pyudev.model_id = product_id_str
        mock_pyudev.dormant = False
        mock_pyudev.delay = 0.1
        wait_delay = mock_pyudev.delay * 2

        # This VID and PID must match the above
        mock_monitor = PyUdevDeviceMonitor(vendor_id,
                                           product_id,
                                           udev_module=mock_pyudev,
                                           logger=self._logger)
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      add_event_handler=_add_handler,
                                      remove_event_handler=_remove_handler,
                                      logger=self._logger)
        controller.start()
        self.assertTrue(controller.running)

        # Wait for the handlers to be invoked
        add_event.wait(wait_delay)
        remove_event.wait(wait_delay)

        # Shut down
        controller.stop()
        self.assertFalse(controller.running)

        # Test after stopping so that we don't hang the test if an
        # assertion failed
        self.assertTrue(add_event.is_set(),
                        'Add handler must not be invoked')
        self.assertTrue(remove_event.is_set(),
                        'Remove handler must not be invoked')
        verify(mock_device, times=2).open()
        verify(mock_device, times=1).close()

    def test_send_when_not_open_must_fail(self):
        '''
        Test that sending a command when the device is not open will fail.
        '''
        mock_monitor = mock()
        mock_device = mock()
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      logger=self._logger)
        when(mock_device).is_open().thenReturn(False)
        self.assertFalse(controller.send('foo'))
        verify(mock_device, times=0).send(any(), any())

    def test_send_when_open_send_must_fail(self):
        '''
        Generate an IOError on send.
        '''
        mock_monitor = mock()
        mock_device = mock()
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      logger=self._logger)
        when(mock_device).is_open().thenReturn(True)
        when(mock_device).send(any()).thenRaise(IOError())
        when(mock_device).get_packet_size().thenReturn(64)
        self.assertFalse(controller.send('foo'))
        verify(mock_device, times=1).send(any())
        verify(mock_device, times=0).recv()

    def test_send_recv_must_fail(self):
        '''
        Generate an IOError on receive.
        '''
        mock_monitor = mock()
        mock_device = mock()
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      logger=self._logger)
        when(mock_device).is_open().thenReturn(True)
        when(mock_device).receive().thenRaise(IOError())
        when(mock_device).get_packet_size().thenReturn(64)
        self.assertFalse(controller.send('foo'))
        verify(mock_device, times=1).send(any())
        verify(mock_device, times=1).receive()

    def test_send_command_not_understood(self):
        '''
        Test that device did NOT understand the command.
        '''
        mock_monitor = mock()
        mock_device = mock()
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      logger=self._logger)
        when(mock_device).is_open().thenReturn(True)
        data = 'nak' + '\0' * (64 - len('nak'))
        when(mock_device).receive().thenReturn(data)
        when(mock_device).get_packet_size().thenReturn(64)
        self.assertFalse(controller.send('foo'))
        verify(mock_device, times=1).send(any())
        verify(mock_device, times=1).receive()

    def test_send_command_understood(self):
        '''
        Test that the device understood the command.
        '''
        mock_monitor = mock()
        mock_device = mock()
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      logger=self._logger)
        when(mock_device).is_open().thenReturn(True)
        data = 'ack' + '\0' * (64 - len('ack'))
        when(mock_device).receive().thenReturn(data)
        when(mock_device).get_packet_size().thenReturn(64)
        self.assertTrue(controller.send('foo'))
        verify(mock_device, times=1).send(any())
        verify(mock_device, times=1).receive()

    def test_without_handlers_must_still_open_and_close_device(self):
        '''
        Test that, without handlers, the device gets opened and closed.
        '''
        # Setup
        mock_monitor = MockDeviceMonitor(dormant=True)
        mock_device = mock()
        when(mock_device).get_vendor_id().thenReturn(0)
        when(mock_device).get_product_id().thenReturn(0)
        when(mock_device).is_open().thenReturn(True)
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      logger=self._logger)

        # Execute
        controller.start()
        self.assertTrue(controller.running)
        controller.stop()
        self.assertFalse(controller.running)

        # Verify mocks
        verify(mock_device, times=1).open()
        verify(mock_device, times=1).close()

    @unittest.skip
    def test_manually_with_different_device_modules_and_managers(self):
        '''
        Manual testing: Blink all lights a few times. You must be able to
        connect and disconnect the device while executing. It doesn't really
        matter whether the device is initially connected or disconnected.
        '''
        # Overriding the default log level so that the instructions are clear
        # and not obfuscated by the many debug messages.
        self._logger.setLevel('INFO')

        # You must enable only one of these
        use_module = 'pyusb'
        #use_module = 'teensyrawhid'
        # And one of these
        use_monitor = 'pyudev'
        #use_monitor = 'polling_device_manager'

        # Basics
        vendor_id = 0x16c0
        product_id = 0x0486
        add_timeout_message = 'The add event must have been invoked'
        remove_timeout_message = 'The remove event must have been invoked'
        iterations = 3
        event_delay = 30
        blink_delay = 0.5
        running = False
        # Trick to get past the closure: The pointer of the states dictionary
        # can't changed, but its data can. :-)
        states = {'paused': True}

        # Select the module to test
        if use_module == 'pyusb':
            interface_number = 1
            device = whatsthatlight.devices.PyUsbDevice(vendor_id,
                                                        product_id,
                                                        interface_number)
        elif use_module == 'teensyrawhid':
            usage_page = 0xffc9
            usage = 0x0004
            device = whatsthatlight.devices.TeensyDevice(vendor_id,
                                                         product_id,
                                                         usage_page,
                                                         usage)
        else:
            raise Exception('Invalid USB device module specified')

        # Select the device manager to test
        if use_monitor == 'pyudev':
            monitor = PyUdevDeviceMonitor(vendor_id,
                                          product_id,
                                          pyudev,
                                          logger=self._logger)
        elif use_monitor == 'polling':
            monitor = None
        else:
            raise Exception('Invalid device manager specified')

        # Execution controllers
        add_event = Event()
        remove_event = Event()
        paused_event = Event()
        add_event.clear()
        remove_event.clear()
        paused_event.clear()

        # Handlers and helpers
        def _add_handler():
            states['paused'] = False
            paused_event.set()
            add_event.set()
            self._logger.debug('Invoked')

        def _remove_handler():
            paused_event.clear()
            states['paused'] = True
            remove_event.set()
            self._logger.debug('Invoked')

        def _run():
            self._logger.debug('Entering run loop')
            toggle = True
            while running:
                if states['paused']:
                    self._logger.debug('Pausing run loop')
                    paused_event.wait(event_delay)
                    self._logger.debug('Resuming run loop')
                # No point asserting sent data if the device gets
                # disconnected while communicating with it -- it's
                # likely to fail.
                if toggle:
                    success = (controller.send('red=on\n') and
                               controller.send('green=on\n') and
                               controller.send('yellow=on\n'))
                    self._logger.debug('All on: {0}'.format(success))
                else:
                    success = (controller.send('red=off\n') and
                               controller.send('green=off\n') and
                               controller.send('yellow=off\n'))
                    self._logger.debug('All off: {0}'.format(success))
                toggle = not toggle
                sleep(blink_delay)
            self._logger.debug('Exiting run loop')

        # Setup
        thread = Thread(target=_run)
        controller = DeviceController(device,
                                      usb_transfer_types.RAW,
                                      monitor,
                                      add_event_handler=_add_handler,
                                      remove_event_handler=_remove_handler,
                                      logger=self._logger)
        # Start everything
        controller.start()
        self.assertTrue(controller.running)
        running = True
        thread.start()

        # Ensure a clean shutdown as to not hang the test unnecessarily
        try:
            i = 0
            while i < iterations:
                # Wait until device connected
                self._logger.info('Waiting for device to be connected')
                add_event.wait(event_delay)
                self.assert_(add_event.is_set(), add_timeout_message)
                add_event.clear()

                # Wait until device disconnected
                self._logger.info('Waiting for device to be disconnected')
                remove_event.wait(event_delay)
                self.assert_(remove_event.is_set(), remove_timeout_message)
                remove_event.clear()

                # Next iteration
                i += 1

        except AssertionError:
            raise
        finally:
            # Stop everything
            running = False
            thread.join()
            controller.stop()
            self.assertFalse(controller.running)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
