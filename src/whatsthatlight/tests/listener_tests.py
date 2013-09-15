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
import threading

# Local imports
from whatsthatlight.listener import Listener
from whatsthatlight.common import utils
from whatsthatlight.common import logger


class Test(unittest.TestCase):

    def setUp(self):
        '''
        Setup.
        '''
        self._logger = logger.get_logger('src/whatsthatlight/logger.conf')

        # Use this line to run single test
        #self._logger = whatsthatlight.common.logger.get_logger('../logger.conf')

    def test_start_and_stop(self):
        '''
        Basic start and stop test.
        '''
        listener = Listener(self._logger)
        listener.start()
        self.assertTrue(listener.running)
        listener.stop()
        self.assertFalse(listener.running)

    def test_start_and_start_again(self):
        '''
        Trying to start twice must not fail.
        '''
        listener = Listener(self._logger)
        listener.start()
        self.assertTrue(listener.running)
        listener.start()
        self.assertTrue(listener.running)
        listener.stop()
        self.assertFalse(listener.running)

    def test_stop_and_stop_again(self):
        '''
        Trying to stop twice must not fail.
        '''
        listener = Listener(self._logger)
        listener.start()
        self.assertTrue(listener.running)
        listener.stop()
        self.assertFalse(listener.running)
        listener.stop()
        self.assertFalse(listener.running)

    def test_listening(self):
        '''
        Basic listening test by connecting to the listener.
        '''
        # Trick to synchronise the the sending and receiving of data.
        event = threading.Event()
        dataTx = []
        dataRx = []

        def handler(data):
            '''
            Dummy handler to catch data received on the socket.
            :param data: the data received
            '''
            dataRx.append(data)

            # The test can proceed
            event.set()

        # Setup
        address = '0.0.0.0'
        port = 10000
        listener = Listener(self._logger, address, port, handler)
        listener.start()
        self.assertTrue(listener.running)

        # Run the test
        try:
            for i in range(0, 10):
                data = 'test' + str(i)
                dataTx.append(data)
                event.clear()
                utils.send(address, port, data)
                event.wait(10)
        except Exception, e:
            self._logger.exception(e)
            raise
        finally:
            listener.stop()
            self.assertFalse(listener.running)

        # Test the results
        for i in range(0, 2):
            self.assertEqual(dataRx[i], dataTx[i])

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
