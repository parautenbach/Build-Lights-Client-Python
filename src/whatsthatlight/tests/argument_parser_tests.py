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
# limitations under the License..

# System imports
import shutil
import subprocess
import sys
import unittest

# Local imports
from whatsthatlight.common import version, argument_parser


class Test(unittest.TestCase):

    def setUp(self):
        '''
        Setup.
        '''
        script = 'mock_argument_parser_console.py'
        shutil.copy(script, '../..')
        self._py_executable = sys.executable
        self._console_script = 'src/' + script

    def test_fails_no_command_line(self):
        '''
        Fails with help if no command line.
        '''
        self.assertRaises(SystemExit, argument_parser.get_arguments)

    def test_print_usage(self):
        '''
        Check that an error is raised if not all command line requirements
        are met.
        '''
        # No config; must print usage; return 2 for command line syntax error
        process = subprocess.Popen([self._py_executable, self._console_script],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        (_, error) = process.communicate()
        self.assertEqual(2, process.returncode)
        self.assertRegexpMatches(error, 'too few arguments')

    def test_get_help(self):
        '''
        Check that help gets issued (this test obviously tests a dependency
        which is generally not done; I'm experimenting here).
        '''
        help_options = ['-h', '--help']
        for h in help_options:
            process = subprocess.Popen([self._py_executable,
                                        self._console_script,
                                        h],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            (output, _) = process.communicate()
            self.assertEqual(0, process.returncode)
            self.assertRegexpMatches(output, 'usage:')
            self.assertRegexpMatches(output, 'positional arguments:')
            self.assertRegexpMatches(output, 'optional arguments:')

    def test_check_version(self):
        '''
        Check that the correct version is reported.
        '''
        process = subprocess.Popen([self._py_executable,
                                    self._console_script,
                                    '-v'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        (_, error) = process.communicate()
        self.assertEqual(0, process.returncode)
        self.assertEqual(version.VERSION, error.split()[-1])

    def test_conf(self):
        '''
        Test that a config file can be passed as a parameter.
        '''
        conf = 'no_such_config.conf'
        process = subprocess.Popen([self._py_executable,
                                    self._console_script,
                                    conf],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        (output, _) = process.communicate()
        self.assertEqual(0, process.returncode)
        self.assertRegexpMatches(output, conf)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
