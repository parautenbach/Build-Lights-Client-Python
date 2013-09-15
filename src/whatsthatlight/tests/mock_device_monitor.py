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
from threading import Thread
from time import sleep


class MockDeviceMonitor(object):

    def __init__(self,
                 dormant=False,
                 delay=1):
        self._dormant = dormant
        self.event_handlers = {'add': None,
                               'remove': None}
        self._thread = Thread(target=self._run)

    def start(self):
        self._thread.start()

    def stop(self):
        self._thread.join()

    def _run(self):
        if self._dormant:
            return
        sleep(self._delay)
        self._get_add_event_handler()()
        sleep(self._delay)
        self._get_remove_event_handler()()

    def _get_add_event_handler(self):
        return self.event_handlers['add']

    def set_add_event_handler(self, handler):
        self.event_handlers['add'] = handler

    def _get_remove_event_handler(self):
        return self.event_handlers['remove']

    def set_remove_event_handler(self, handler):
        self.event_handlers['remove'] = handler
