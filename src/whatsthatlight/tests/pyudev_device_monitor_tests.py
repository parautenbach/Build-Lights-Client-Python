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
from whatsthatlight.common import logger
from whatsthatlight.device_monitors import PyUdevDeviceMonitor

# Third-party imports
import pyudev


class Test(unittest.TestCase):
    '''
    PyUdev device monitor tests.
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
        monitors = PyUdevDeviceMonitor(0, 0, pyudev, logger=self._logger)
        monitors.start()
        self.assertTrue(monitors.running)
        monitors.stop()
        self.assertFalse(monitors.running)

    def test_start_and_start_again(self):
        '''
        Trying to start twice must not fail.
        '''
        monitors = PyUdevDeviceMonitor(0, 0, pyudev, logger=self._logger)
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
        monitors = PyUdevDeviceMonitor(0, 0, pyudev, logger=self._logger)
        monitors.start()
        self.assertTrue(monitors.running)
        monitors.stop()
        self.assertFalse(monitors.running)
        monitors.stop()
        self.assertFalse(monitors.running)
