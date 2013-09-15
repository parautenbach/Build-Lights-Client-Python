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

# System import
import unittest
from threading import Event
from time import sleep

# Local imports
import mock_pyudev
from whatsthatlight import notifier_client
from whatsthatlight.common import logger
from whatsthatlight.common import utils
from whatsthatlight.common import fields
from whatsthatlight.common import packets
from whatsthatlight.common import parser
from whatsthatlight.common import request_types
from whatsthatlight.common import usb_transfer_types
from whatsthatlight.common.requests import StatusRequest
from whatsthatlight.device_controller import DeviceController
from whatsthatlight.device_monitors import PyUdevDeviceMonitor
from whatsthatlight.listener import Listener
from whatsthatlight.tests import mock_device_controller

# Third-party imports
from mockito import mock, when, any


class Test(unittest.TestCase):
    '''
    The the notifier client.
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
        mock_device_controller = mock()
        client = notifier_client.NotifierClient('foo',
                                                mock_device_controller,
                                                logger=self._logger)
        client.start()
        self.assertTrue(client.running)
        client.stop()
        self.assertFalse(client.running)

    def test_start_and_start_again(self):
        '''
        Trying to start twice must not fail.
        '''
        mock_device_controller = mock()
        client = notifier_client.NotifierClient('foo',
                                                mock_device_controller,
                                                logger=self._logger)
        client.start()
        self.assertTrue(client.running)
        client.start()
        self.assertTrue(client.running)
        client.stop()
        self.assertFalse(client.running)

    def test_stop_and_stop_again(self):
        '''
        Trying to stop twice must not fail.
        '''
        mock_device_controller = mock()
        client = notifier_client.NotifierClient('foo',
                                                mock_device_controller,
                                                logger=self._logger)
        client.start()
        self.assertTrue(client.running)
        client.stop()
        self.assertFalse(client.running)
        client.stop()
        self.assertFalse(client.running)

    def test_listening(self):
        '''
        Check that the client started its listener.
        '''
        # Setup
        address = '0.0.0.0'
        port = 10010
        mock_device_controller = mock()
        client = notifier_client.NotifierClient('foo',
                                                mock_device_controller,
                                                logger=self._logger,
                                                address=address,
                                                port=port)
        client.start()
        self.assertTrue(client.running)

        # Run the test
        connected = False
        try:
            data = 'test'
            utils.send(address, port, data)
            connected = True
        except Exception, e:
            self._logger.exception(e)
        finally:
            client.stop()
            self.assertFalse(client.running)
        self.assertTrue(connected, 'Could not connect to listener')

    def test_registration(self):
        '''
        Test that the client registers when a USB device gets connected.
        '''
        # Device details
        vendor_id_str = '0a1b'
        vendor_id = int(vendor_id_str, 16)
        product_id_str = '2c3d'
        product_id = int(product_id_str, 16)

        # Execution controllers
        server_event = Event()
        server_event.clear()

        # Config
        host = 'localhost'
        port = 9192
        username = 'bar'
        server_address = host
        server_port = 9191

        # Mocks and other parameters
        mock_pyudev.vendor_id = vendor_id_str
        mock_pyudev.model_id = product_id_str
        mock_pyudev.dormant = False
        mock_pyudev.delay = 0.1
        wait_delay = mock_pyudev.delay * 2
        mock_monitor = PyUdevDeviceMonitor(vendor_id,
                                           product_id,
                                           udev_module=mock_pyudev,
                                           logger=self._logger)
        mock_device = mock()
        when(mock_device).get_vendor_id().thenReturn(vendor_id)
        when(mock_device).get_product_id().thenReturn(product_id)
        server_data = []

        def _server_handler(data):
            self._logger.debug('Invoked')
            server_data.append(data)
            server_event.set()

        # Client-side instances
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      logger=self._logger)
        client = notifier_client.NotifierClient(username,
                                                controller,
                                                address=host,
                                                port=port,
                                                server_address=server_address,
                                                server_port=server_port,
                                                logger=self._logger)

        # Dummy server instance for receiving a registration request
        server_listener = Listener(address=server_address,
                                   port=server_port,
                                   handler=_server_handler,
                                   logger=self._logger)
        # Startup
        server_listener.start()
        self.assertTrue(server_listener.running)
        client.start()
        self.assertTrue(client.running)
        self.assertTrue(controller.running)

        # mock_pyudev will raise an add event, which should result in a
        # registration request, which is what we're waiting for
        server_event.wait(wait_delay)
        send_failed = False
        try:
            utils.send(host, port, '')
        except:
            send_failed = True

        # Shutdown
        client.stop()
        self.assertFalse(client.running)
        self.assertFalse(controller.running)
        server_listener.stop()
        self.assertFalse(server_listener.running)

        # Test the results
        self.assertTrue(server_event.is_set(), 'Registration was not in time')
        self.assertFalse(send_failed, 'The host address is invalid')

        # Expected output similar to:
        # requesttypeid=1;hostname=bar;username=foo!
        command = server_data[0]
        self.assertTrue(command.endswith(packets.TERMINATOR))
        self.assertEqual(1, command.count(packets.TERMINATOR))
        self.assertEqual(2, command.count(packets.COMMAND_SEPARATOR))
        self.assertEqual(3, command.count(packets.FIELD_SEPARATOR))
        self.assertEqual(1, command.count('{0}={1}'.
                                          format(fields.REQUEST_TYPE_ID,
                                                 request_types.REGISTER)))
        self.assertEqual(1, command.count('{0}={1}'.
                                          format(fields.HOSTNAME,
                                                 host)))
        self.assertEqual(1, command.count('{0}={1}'.
                                          format(fields.USERNAME,
                                                 username)))

    def test_registration_retry(self):
        '''
        Test that the client registers when a USB device gets connected.
        '''
        # Device details
        vendor_id_str = '0a1b'
        vendor_id = int(vendor_id_str, 16)
        product_id_str = '2c3d'
        product_id = int(product_id_str, 16)

        # Execution controllers
        server_event = Event()
        server_event.clear()

        # Config
        host = 'localhost'
        port = 9192
        username = 'bar'
        server_address = host
        server_port = 9191
        retry_period = 1

        # Mocks and other parameters
        mock_pyudev.vendor_id = vendor_id_str
        mock_pyudev.model_id = product_id_str
        mock_pyudev.dormant = True
        #mock_pyudev.delay = 0.1
        start_delay = retry_period
        event_delay = start_delay * 2
        mock_monitor = PyUdevDeviceMonitor(vendor_id,
                                           product_id,
                                           udev_module=mock_pyudev,
                                           logger=self._logger)
        mock_device = mock()
        when(mock_device).get_vendor_id().thenReturn(vendor_id)
        when(mock_device).get_product_id().thenReturn(product_id)
        when(mock_device).is_open().thenReturn(True)
        when(mock_device).send(any())
        when(mock_device).receive().thenReturn('')
        when(mock_device).get_packet_size().thenReturn(64)
        server_data = []

        def _server_handler(data):
            self._logger.debug('Invoked')
            server_data.append(data)
            server_event.set()

        # Client-side instances
        controller = DeviceController(mock_device,
                                      usb_transfer_types.RAW,
                                      mock_monitor,
                                      logger=self._logger)
        client = notifier_client.NotifierClient(username,
                                                controller,
                                                address=host,
                                                port=port,
                                                server_address=server_address,
                                                server_port=server_port,
                                                retry_period=retry_period,
                                                logger=self._logger)

        # Dummy server instance for receiving a registration request
        server_listener = Listener(address=server_address,
                                   port=server_port,
                                   handler=_server_handler,
                                   logger=self._logger)
        # Startup
        client.start()
        self.assertTrue(client.running)
        self.assertTrue(controller.running)

        # Delay server startup to test the registration retry
        sleep(start_delay)
        server_listener.start()
        self.assertTrue(server_listener.running)

        # mock_pyudev will raise an add event, which should result in a
        # registration request, which is what we're waiting for
        server_event.wait(event_delay * 2)
        send_failed = False
        try:
            utils.send(host, port, '')
        except:
            send_failed = True

        # Shutdown
        client.stop()
        self.assertFalse(client.running)
        self.assertFalse(controller.running)
        server_listener.stop()
        self.assertFalse(server_listener.running)

        # Test the results
        self.assertTrue(server_event.is_set(), 'Registration was not in time')
        self.assertFalse(send_failed, 'The host address is invalid')

        # Expected output similar to:
        # requesttypeid=1;hostname=bar;username=foo!
        command = server_data[0]
        self.assertTrue(command.endswith(packets.TERMINATOR))
        self.assertEqual(1, command.count(packets.TERMINATOR))
        self.assertEqual(2, command.count(packets.COMMAND_SEPARATOR))
        self.assertEqual(3, command.count(packets.FIELD_SEPARATOR))
        self.assertEqual(1, command.count('{0}={1}'.
                                          format(fields.REQUEST_TYPE_ID,
                                                 request_types.REGISTER)))
        self.assertEqual(1, command.count('{0}={1}'.
                                          format(fields.HOSTNAME,
                                                 host)))
        self.assertEqual(1, command.count('{0}={1}'.
                                          format(fields.USERNAME,
                                                 username)))

    def test_set_unknown_status_on_startup_and_shutdown(self):
        '''
        Check that the client sets the USB device's status to
        unknown on startup and shutdown.
        '''
        # Setup
        address = '0.0.0.0'
        port = 10110
        command_list = []

        # Capture commands sent to the USB device
        def _send_handler(command):
            self._logger.debug('Invoked')
            command_list.append(command)

        # Construct the client
        mock_dc = mock_device_controller.DeviceController(_send_handler,
                                                          logger=self._logger)
        client = notifier_client.NotifierClient('foo',
                                                mock_dc,
                                                address=address,
                                                port=port,
                                                logger=self._logger)

        # On both start-up and shutdown, the device must be initialised
        # with all LEDs on, which indicates an unknown status
        client.start()
        self.assertTrue(client.running)
        client.stop()
        self.assertFalse(client.running)

        self.assertTrue(len(command_list) == 2,
                        'There must be exactly one command on start-up '
                        'and one on shutdown')

        # Split correctly generates an empty string after the last \n
        expected = ['red=on', 'green=on', 'yellow=on', '']
        for command in command_list:
            self.assertTrue(command.count('\n'), 3)
            self.assertListEqual(expected, command.split('\n'))

    def test_handle_status_down_request(self):
        '''
        Check that the client can handle status down requests.
        '''
        # Setup
        address = '0.0.0.0'
        port = 10110
        command_list = []

        # Capture commands sent to the USB device
        def _send_handler(command):
            self._logger.debug('Invoked')
            command_list.append(command)

        # Construct the client
        mock_dc = mock_device_controller.DeviceController(_send_handler,
                                                          logger=self._logger)
        client = notifier_client.NotifierClient('foo',
                                                mock_dc,
                                                address=address,
                                                port=port,
                                                logger=self._logger)

        # Here we also send a server down notification as if from
        # the notification server.
        client.start()
        self.assertTrue(client.running)
        request = StatusRequest(False)
        client.handle_request(request)
        client.stop()
        self.assertFalse(client.running)

        # Test the number of commands/command batches sent
        self.assertTrue(len(command_list) == 3,
                        'There must be exactly three commands')

        # Split correctly generates an empty string after the last \n
        expected = ['red=on', 'green=on', 'yellow=on', '']
        for command in command_list:
            self.assertTrue(command.count('\n'), 3)
            self.assertListEqual(expected, command.split('\n'))

if __name__ == "__main__":
    unittest.main()
