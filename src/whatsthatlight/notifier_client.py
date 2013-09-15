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

# Local imports
import listener
from common import config
from common import parser
from common import requests
from common import utils
from common import version
from common import usb_protocol_types


class NotifierClient:
    '''
    Notifier client for receiving events from the notification server.
    '''

    def __init__(self,
                 username,
                 device_controller,
                 address=config.CLIENT_ADDRESS_DEFAULT,
                 port=config.CLIENT_PORT_DEFAULT,
                 server_address=config.SERVER_ADDRESS_DEFAULT,
                 server_port=config.SERVER_PORT_DEFAULT,
                 retry_period=5,
                 usb_protocol_type=usb_protocol_types.DAS_BLINKENLICHTEN,
                 logger=logging.basicConfig()):
        '''
        Constructor.
        :param username: the user that this client represents
        :param device_controller: the controller for the lights device
        :param address: the address to listen on; defaults to all interfaces
        :param port: the port to listen on
        :param server_address: the notification server's address
        :param server_port: the notification server's port
        :param retry_period: registration retry period in seconds
        :param usb_protocol_type: the USB protocol used to communicate
        :param logger: local logger instance
        '''
        self._logger = logger
        self._address = address
        self._username = username
        self._server_address = server_address
        self._server_port = server_port
        self._retry_period = retry_period
        self._retry_timer = None
        self._usb_protocol_type = usb_protocol_type
        self._listener = listener.Listener(logger=logger,
                                           address=address,
                                           port=port,
                                           handler=self.handle_data)

        def _device_add_handler():
            self._logger.debug('Invoked')
            self.register()

        def _device_remove_handler():
            self._logger.debug('Invoked')
            self._stop_registration_timer()

        self._device_controller = device_controller
        self._device_controller.set_add_event_handler(_device_add_handler)
        (self._device_controller.
         set_remove_event_handler(_device_remove_handler))
        self.running = False
        self._runLock = threading.Lock()

    def start(self):
        '''
        Start the client.
        '''
        self._logger.info("Client starting (version %s)",
                          version.VERSION)
        with self._runLock:
            if self.running:
                self._logger.warn("Client already started")
                return
            self._device_controller.start()
            self._listener.start()
            # Status is unknown on start-up
            request = requests.StatusRequest(False)
            self.handle_request(request)
            self._logger.info("Client started")
            self.running = True

    def stop(self):
        '''
        Stop the client.
        '''
        self._logger.info("Client stopping")
        with self._runLock:
            if not self.running:
                self._logger.warn("Client already stopped")
                return
            self._stop_registration_timer()
            # Status is unknown after shutdown
            request = requests.StatusRequest(False)
            self.handle_request(request)
            self._device_controller.stop()
            self._listener.stop()
            self._logger.info("Client stopped")
            self.running = False

    def register(self):
        '''
        Register this notifier client with the server.
        '''
        self._stop_registration_timer()
        self._logger.info('Registering user %s with host %s',
                          self._username,
                          self._address)
        command = parser.encode(requests.RegistrationRequest(self._address,
                                                             self._username))
        try:
            self._logger.debug('Registering with {0} on port {1}'.
                               format(self._server_address,
                                      self._server_port))
            utils.send(self._server_address, self._server_port, command)
        except Exception, e:
            self._logger.warn('Could not register ({0}); '
                              'will retry in {1} second(s)'.
                              format(e, self._retry_period))
            self._start_registration_timer()

    def _start_registration_timer(self):
        '''
        Start the registration timer.
        '''
        self._logger.debug('Starting a new registration timer')
        self._retry_timer = threading.Timer(self._retry_period,
                                            self.register)
        self._retry_timer.start()

    def _stop_registration_timer(self):
        '''
        Stop the registration timer.
        '''
        if not self._retry_timer is None:
            self._logger.debug('Stopping the registration timer')
            self._retry_timer.cancel()

    def handle_data(self, data):
        '''
        Handle data received from the notification server.
        :param data: The raw data
        '''
        try:
            self._logger.debug('Data received: {0}'.format(data))
            request = parser.decode(data)
            self.handle_request(request)
        except Exception, e:
            self._logger.exception(e)

    def handle_request(self, request):
        '''
        Handle a request after decoded from data.
        :param request: the decoded request
        '''
        try:
            if (self._usb_protocol_type ==
                usb_protocol_types.DAS_BLINKENLICHTEN):
                command = parser.translate(request)
            elif (self._usb_protocol_type ==
                usb_protocol_types.BLINK1):
                    command = parser.translate_for_blink1(request)
            self._device_controller.send(command)
        except Exception, e:
            self._logger.exception(e)
