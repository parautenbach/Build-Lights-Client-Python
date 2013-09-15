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
from whatsthatlight.common import parser
from whatsthatlight.common import requests
from whatsthatlight.common import fields
from whatsthatlight.common import packets
from whatsthatlight.common import request_types
from whatsthatlight.common.requests import InvalidRequestException


class Test(unittest.TestCase):

    def setUp(self):
        '''
        Setup.
        '''
        self._logger = logger.get_logger('src/whatsthatlight/logger.conf')

        # Use this line to run single test
        #self._logger = logger.get_logger('../logger.conf')

    def test_encode_valid_registration_request(self):
        '''
        Test the encoding of a valid registration request.
        '''
        username = 'foo'
        hostname = 'bar'
        request = requests.RegistrationRequest(hostname,
                                               username)
        command = parser.encode(request)

        # Expected output similar to:
        # requesttypeid=1;hostname=bar;username=foo!
        self.assertTrue(command.endswith(packets.TERMINATOR))
        self.assertEqual(1, command.count(packets.TERMINATOR))
        self.assertEqual(2, command.count(packets.COMMAND_SEPARATOR))
        self.assertEqual(3, command.count(packets.FIELD_SEPARATOR))
        self.assertEqual(1, command.count('{0}={1}'.
                                          format(fields.REQUEST_TYPE_ID,
                                                 request_types.REGISTER)))
        self.assertEqual(1, command.count('{0}={1}'.
                                          format(fields.HOSTNAME,
                                                 hostname)))
        self.assertEqual(1, command.count('{0}={1}'.
                                          format(fields.USERNAME,
                                                 username)))

    def test_encode_invalid_request(self):
        '''
        Test the encoding of an invalid request.
        '''
        request = object()
        self.assertRaises(InvalidRequestException, parser.encode, request)

    def test_encode_valid_status_request_status_up(self):
        '''
        Test the encoding of a valid status request.
        '''
        self._encode_valid_status_request_status(True)

    def test_encode_valid_status_request_status_down(self):
        '''
        Test the encoding of a valid status request.
        '''
        self._encode_valid_status_request_status(False)

    def _encode_valid_status_request_status(self, status):
        '''
        Helper.
        :param status: True if server or client is up
        '''
        request = requests.StatusRequest(status)
        command = parser.encode(request)

        # Expected output similar to:
        self.assertTrue(command.endswith(packets.TERMINATOR))
        self.assertEqual(1, command.count(packets.TERMINATOR))
        self.assertEqual(1, command.count(packets.COMMAND_SEPARATOR))
        self.assertEqual(2, command.count(packets.FIELD_SEPARATOR))
        self.assertEqual(1, command.count('{0}={1}'.
                                          format(fields.REQUEST_TYPE_ID,
                                                 request_types.SERVER_STATUS)))
        self.assertEqual(1, command.count('{0}={1}'.
                                          format(fields.SERVER_STATUS,
                                                 int(status))))

    def test_decode_status_request_is_up(self):
        '''
        Deserialise a status request.
        '''
        self._decode_status_request(True)

    def test_decode_status_request_is_down(self):
        '''
        Deserialise a status request.
        '''
        self._decode_status_request(False)

    def _decode_status_request(self, status):
        '''
        Deserialise a status request.
        '''
        data = 'requesttypeid=4;status={0}!'.format(int(status))
        request = parser.decode(data)
        self.assertIsInstance(request, requests.StatusRequest)
        self.assertEqual(int(status), request.is_up())

    def test_translate_status_request_is_up(self):
        '''
        Cannot translate a server up request.
        '''
        request = requests.StatusRequest(True)
        self.assertRaises(InvalidRequestException, parser.translate, request)

    def test_translate_status_request_is_down(self):
        '''
        Can only translate a server down request.
        '''
        request = requests.StatusRequest(False)
        command = parser.translate(request)

        # Split correctly generates an empty string after the last \n
        expected = ['red=on', 'green=on', 'yellow=on', '']
        self.assertTrue(command.count('\n'), 3)
        self.assertListEqual(expected, command.split('\n'))

    def test_decode_invalid_request(self):
        '''
        Invalid request.
        '''
        # No type ID
        self.assertRaises(InvalidRequestException,
                          parser.decode,
                          'foo=bar!')
        # Invalid type ID
        self.assertRaises(InvalidRequestException,
                          parser.decode,
                          'requesttypeid=0!')
        # Type ID not an int
        self.assertRaises(InvalidRequestException,
                          parser.decode,
                          'requesttypeid=foo!')
        # Ambiguous key
        self.assertRaises(InvalidRequestException,
                          parser.decode,
                          'requesttypeid=1;requesttypeid=2!')
        # Duplicate key
        self.assertRaises(InvalidRequestException,
                          parser.decode,
                          'requesttypeid=1;requesttypeid=1!')

    def test_translate_invalid_request(self):
        '''
        Cannot translate an invalid request.
        '''
        self.assertRaises(InvalidRequestException,
                          parser.translate,
                          None)
        self.assertRaises(InvalidRequestException,
                          parser.translate,
                          requests.BaseRequest())

    def test_decode_build_active_request(self):
        '''
        Decode build active requests.
        '''
        self._decode_build_active_request(True)
        self._decode_build_active_request(False)

    def _decode_build_active_request(self, builds_active):
        '''
        Decode build active requests.
        '''
        data = ('requesttypeid=3;buildsactive={0}!'.
                format(str(int(builds_active))))
        request = parser.decode(data)
        self.assertIsInstance(request, requests.BuildActiveRequest)
        self.assertEqual(request_types.BUILD_ACTIVE, request.get_type())
        self.assertEqual(builds_active, request.is_build_active())

    def test_translate_build_active_request(self):
        '''
        Translate a build active request.
        '''
        self._translate_build_active_request(True, 'on')
        self._translate_build_active_request(False, 'off')

    def _translate_build_active_request(self, active, expected):
        '''
        Translate a build active request.
        :param active: True if any builds active, false otherwise
        :param expected: on if True, off otherwise
        '''
        command = parser.translate(requests.BuildActiveRequest(active))
        self.assertEqual('yellow={0}\n'.format(expected), command)

    def test_decode_attention_request(self):
        '''
        Decode attention requests.
        '''
        # Priority attention
        self._decode_attention_request(True, True)
        # Attention, no priority
        self._decode_attention_request(True, False)
        # No attention, priority -- impossible
        self._decode_attention_request(False, True)
        # No attention (and hence no priority)
        self._decode_attention_request(False, False)

    def _decode_attention_request(self, attention, priority):
        '''
        Decode attention requests.
        '''
        data = ('requesttypeid=2;attention={0};priority={1}!'.
                format(str(int(attention)), str(int(priority))))
        if not attention and priority:
            self.assertRaises(InvalidRequestException, parser.decode, data)
            return
        request = parser.decode(data)
        self.assertIsInstance(request, requests.AttentionRequest)
        self.assertEqual(request_types.ATTENTION, request.get_type())
        self.assertEqual(attention, request.is_required())
        self.assertEqual(priority, request.is_priority())

    def test_translate_attention_request(self):
        '''
        Translate a build active request.
        '''
        self._translate_attention_request(True, True)
        self._translate_attention_request(True, False)
        self._translate_attention_request(False, False)

    def _translate_attention_request(self, attention, priority):
        '''
        Translate a build active request.
        :param attention: True if attention required, false otherwise
        :param priority: True if attention is priority, off otherwise
        '''
        command = parser.translate(requests.AttentionRequest(attention,
                                                             priority))
        command_split = command.split('\n')
        self.assertEquals(command.count('\n'), 2)
        if attention and priority:
            expected = ['red=sos', 'green=off', '']
            self.assertListEqual(expected, command_split)
        elif attention and not priority:
            expected = ['red=on', 'green=off', '']
            self.assertListEqual(expected, command_split)
        elif not attention and not priority:
            expected = ['red=off', 'green=on', '']
            self.assertListEqual(expected, command_split)
        else:
            self.fail('Invalid')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test']
    unittest.main()
