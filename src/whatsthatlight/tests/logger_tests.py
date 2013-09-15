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


class Test(unittest.TestCase):
    '''
    Logger tests.
    '''

    def test_get_logger(self):
        '''
        Test that exception gets raised if config is invalid.
        '''
        self.assertRaises(logger.InvalidLoggerConfigException,
                          logger.get_logger,
                          '')
        self.assertRaises(logger.InvalidLoggerConfigException,
                          logger.get_logger,
                          'random/foo/bar/baz')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
