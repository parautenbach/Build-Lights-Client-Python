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

# The device events will be raised with these attributes
vendor_id = None
model_id = None
dormant = False
delay = 1


class Context(object):

    def __init__(self):
        pass


class Monitor(object):

    def __init__(self):
        pass

    def filter_by(self, subsystem=None, device_type=None):
        pass

    @classmethod
    def from_netlink(cls, context):
        return Monitor()


class MonitorObserver(object):

    def __init__(self, monitor, callback=None, name=None):
        self._callback = callback
        self._thread = Thread(target=self._run)

    def start(self):
        self._thread.start()

    def stop(self):
        self._thread.join()

    def _run(self):
        if dormant:
            return
        device = {'ACTION': None,
                  'ID_VENDOR_ID': vendor_id,
                  'ID_MODEL_ID': model_id}
        sleep(delay)
        device['ACTION'] = 'add'
        self._callback(device)
        sleep(delay)
        device['ACTION'] = 'remove'
        self._callback(device)
