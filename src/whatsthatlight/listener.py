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
import socket
import threading

# Local imports
from common import config
from common import packets
from common import utils


class Listener(object):
    '''
    A socket server listener.
    '''

    def __init__(self,
                 logger=logging.basicConfig(),
                 address=config.CLIENT_ADDRESS_DEFAULT,
                 port=config.CLIENT_PORT_DEFAULT,
                 handler=None):
        '''
        Constructor.
        :param logger: local logger instance
        :param address: the address to listen on; defaults to all interfaces
        :param port: the port to listen on
        :param handler: a method to handle received data
        '''
        self._logger = logger
        self._address = address
        self._port = port
        self._handler = handler
        self.running = False
        self._runLock = threading.Lock()
        self._thread = None
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET,
                                       socket.SO_REUSEADDR,
                                       True)
        self._runningEvent = threading.Event()

    def start(self):
        '''
        Start the listener.
        '''
        self._logger.info("Listener starting")
        with self._runLock:
            if self.running:
                self._logger.warn("Listener already started")
                return
            self._thread = threading.Thread(target=self._run)
            self._logger.info('Server will listen to IP address %s '
                              'on port %i',
                              str(self._address), self._port)
            self._server_socket.bind((self._address, self._port))
            self._server_socket.listen(10)
            self._runningEvent.clear()
            self.running = True
            self._thread.start()
            while not self._runningEvent.is_set():
                self._runningEvent.wait(10)
            self._logger.info("Listener started")

    def stop(self):
        '''
        Stop the listener.
        '''
        self._logger.info("Listener stopping")
        with self._runLock:
            if not self.running:
                self._logger.warn("Listener already stopped")
                return
            self.running = False
            self._logger.debug("Bumping the thread out of the blocking accept")
            try:
                utils.send(self._address, self._port, '')
            except Exception, e:
                self._logger.exception(e)
            self._thread.join()
            self._server_socket.close()
            self._logger.info("Listener stopped")

    def _run(self):
        '''
        Main listener loop.
        '''
        try:
            while self.running:
                if not self._runningEvent.is_set():
                    self._runningEvent.set()
                self._logger.debug("Waiting for connection")
                (client_socket, (address, _)) = self._server_socket.accept()
                self._logger.info('New connection from %s accepted', address)
                data = client_socket.recv(packets.MAX_SIZE)

                # If there's a handler and there's no more data to read,
                # invoke the handler.
                if not self._handler is None and len(data) > 0:
                    self._handler(data)
                client_socket.close()
                self._logger.info('Connection closed')
        except Exception, e:
            self._logger.exception(e)
            raise
