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

# Constants
_ACK = 'ack'
_TIMEOUT = 50
_VENDOR_ID_KEY = 'ID_VENDOR_ID'
_PRODUCT_ID_KEY = 'ID_MODEL_ID'


class DeviceController(object):

    def __init__(self,
                 send_handler=None,
                 logger=logging.basicConfig()):
        self._logger = logger
        self._send_handler = send_handler
        self.running = False
        self._runLock = threading.Lock()

    def start(self):
        self._logger.info("Mock device controller starting")
        with self._runLock:
            if self.running:
                self._logger.warn("Mock device controller already started")
                return
            self._open_device()
            self.running = True
            self._logger.info("Mock device controller started")

    def stop(self):
        self._logger.info("Mock device controller stopping")
        with self._runLock:
            if not self.running:
                self._logger.warn("Mock device controller already stopped")
                return
            self._close_device()
            self.running = False
            self._logger.info("Mock device controller stopped")

    def _get_add_event_handler(self):
        return None

    def set_add_event_handler(self, handler):
        pass

    def _get_remove_event_handler(self):
        return None

    def set_remove_event_handler(self, handler):
        pass

    def _device_is_open(self):
        return self._is_open

    def _open_device(self):
        self._is_open = True

    def _close_device(self):
        self._is_open = False

    def send(self, command):
        if not self._send_handler is None:
            self._send_handler(command)
