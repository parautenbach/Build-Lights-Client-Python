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

# Local imports
import requests
import fields
import led_states
import packets
import request_types
import utils
from requests import InvalidRequestException
from requests import AttentionRequest
from requests import BuildActiveRequest
from requests import StatusRequest


def decode(data):
    '''
    Decode data received from the notification server
    into a type of BaseRequest.
    :param data: the raw data in the format
      <key>=<val>;<key>=<val>;...;<key>=<val>!
    '''
    data_dict = _decompose(data)
    if (_is_request_of_type(data_dict, request_types.
                            SERVER_STATUS)):
        return StatusRequest(_str_to_bool(data_dict[fields.
                                                    SERVER_STATUS]))
    if (_is_request_of_type(data_dict, request_types.BUILD_ACTIVE)):
        return BuildActiveRequest(_str_to_bool(data_dict[fields.
                                                         BUILDS_ACTIVE]))
    if (_is_request_of_type(data_dict, request_types.ATTENTION)):
        return AttentionRequest(_str_to_bool(data_dict[fields.
                                                       ATTENTION_REQUIRED]),
                                _str_to_bool(data_dict[fields.
                                                       ATTENTION_PRIORITY]))
    raise InvalidRequestException('Cannot decode a request of type ID {0}'.
                                  format(data_dict[fields.REQUEST_TYPE_ID]))


def _str_to_bool(s):
    '''
    Cast a integer string to a bool (e.g. '1' => True, '0' => False).
    :param s: the integer string
    '''
    return bool(int(s))


def _is_request_of_type(data_dict, request_type):
    '''
    Check whether a raw request is of a certain type.
    :param data_dict: a data dictionary of decomposed key-value pairs
    :param request_type: a request_types member
    '''
    if (not fields.REQUEST_TYPE_ID in data_dict or
        not data_dict[fields.REQUEST_TYPE_ID].isdigit()):
        raise InvalidRequestException('No or invalid type ID found')
    return (int(data_dict[fields.REQUEST_TYPE_ID]) == int(request_type))


def _decompose(data):
    '''
    Decompose a raw data string into a bunch of key-value pairs.
    :param data: raw socket data
    '''
    if not data.endswith(packets.TERMINATOR):
        raise InvalidRequestException('Malformatted request')
    data_parts = (data.rstrip(packets.TERMINATOR).
                  split(packets.COMMAND_SEPARATOR))
    data_dict = {}
    for part in data_parts:
        (key, val) = part.split(packets.FIELD_SEPARATOR)
        if key in data_dict:
            raise InvalidRequestException('Ambiguous or duplicate type ID')
        data_dict[key] = val
    return data_dict


def encode(request):
    '''
    Encode requests for transmitting over the wire.
    :param request: a request that inherits from requests.BaseRequest
    '''
    if isinstance(request, requests.RegistrationRequest):
        return _encode_reqistration_request(request)
    elif isinstance(request, requests.StatusRequest):
        return _encode_status_request(request)
    raise InvalidRequestException('Cannot encode a request of type {0}'.
                                  format(type(request)))


def _encode_reqistration_request(request):
    '''
    Encode a requests.RegistrationRequest.
    :param request: A registration request.
    '''
    command_tuples = {(fields.REQUEST_TYPE_ID, request.get_type()),
                      (fields.HOSTNAME, request.get_hostname()),
                      (fields.USERNAME, request.get_username())}
    return _assemble_command(command_tuples, packets.TERMINATOR)


def _encode_status_request(request):
    '''
    Encode a requests.StatusRequest.
    :param request: A status request.
    '''
    command_tuples = {(fields.REQUEST_TYPE_ID, request.get_type()),
                      (fields.SERVER_STATUS, int(request.is_up()))}
    return _assemble_command(command_tuples, packets.TERMINATOR)


def translate(request):
    '''
    Translate a request into a command that can be
    understood by the USB device.
    :param request: a request of type BaseRequest
    '''
    if isinstance(request, requests.BuildActiveRequest):
        return _translate_build_active_request(request)
    elif isinstance(request, requests.StatusRequest):
        return _translate_status_request(request)
    elif isinstance(request, requests.AttentionRequest):
        return _translate_attention_request(request)
    raise InvalidRequestException('Cannot translate a request of type {0}'.
                                  format(type(request)))


def translate_for_blink1(request):
    '''
    Translate a request into a command that can be
    understood by a blink(1) USB device.
    :param request: a request of type BaseRequest
    '''
    if isinstance(request, requests.BuildActiveRequest):
        return _translate_build_active_request_for_blink1(request)
    elif isinstance(request, requests.StatusRequest):
        return _translate_status_request_for_blink1(request)
    elif isinstance(request, requests.AttentionRequest):
        return _translate_attention_request_for_blink1(request)
    raise InvalidRequestException('Cannot translate a request of type {0}'.
                                  format(type(request)))


def _translate_attention_request_for_blink1(request):
    '''
    '''
    if request.is_required() or request.is_priority():
        return _assemble_blink1_command({(fields.RED_LED, led_states.ON)})
    else:
        return _assemble_blink1_command({(fields.GREEN_LED, led_states.ON)})


def _translate_build_active_request_for_blink1(request):
    '''
    '''
    if request.is_build_active():
        return _assemble_blink1_command({(fields.YELLOW_LED, led_states.ON)})


def _translate_status_request_for_blink1(request):
    if request.is_up():
        raise InvalidRequestException('Only a client or server down '
                                      'request can be translated')
    return _assemble_blink1_command({(fields.BLUE_LED, led_states.ON)})


def _translate_status_request(request):
    '''
    Translate a StatusRequest. If status is down, switch on all LEDs.
    An up request is not allowed, since it does not make any sense:
    When up, the client must register and the notification server must
    send the latest state for the user.
    :param request: a StatusRequest
    '''
    if request.is_up():
        raise InvalidRequestException('Only a client or server down '
                                      'request can be translated')
    red_command = _assemble_led_command(fields.RED_LED,
                                        led_states.ON)
    green_command = _assemble_led_command(fields.GREEN_LED,
                                          led_states.ON)
    yellow_command = _assemble_led_command(fields.YELLOW_LED,
                                           led_states.ON)
    return ''.join([red_command, green_command, yellow_command])


def _translate_build_active_request(request):
    '''
    Translate a BuildActiveRequest.
    :param request: a BuildActiveRequest
    '''
    if request.is_build_active():
        command_tuples = {(fields.YELLOW_LED, led_states.ON)}
    else:
        command_tuples = {(fields.YELLOW_LED, led_states.OFF)}
    return _assemble_command(command_tuples, packets.ALT_TERMINATOR)


def _translate_attention_request(request):
    '''
    Translate an AttentionRequest.
    :param request: an AttentionRequest
    '''
    if request.is_required() and not request.is_priority():
        red_tuple = {(fields.RED_LED, led_states.ON)}
        green_tuple = {(fields.GREEN_LED, led_states.OFF)}
    elif request.is_required() and request.is_priority():
        red_tuple = {(fields.RED_LED, led_states.SOS)}
        green_tuple = {(fields.GREEN_LED, led_states.OFF)}
    else:
        red_tuple = {(fields.RED_LED, led_states.OFF)}
        green_tuple = {(fields.GREEN_LED, led_states.ON)}
    red_command = _assemble_command(red_tuple, packets.ALT_TERMINATOR)
    green_command = _assemble_command(green_tuple, packets.ALT_TERMINATOR)
    return ''.join([red_command, green_command])


def _assemble_command(command_tuples, terminator):
    '''
    Assemble a list of command tuples into a valid packet. E.g. the list
      [('foo', 'bar'), ('baz', 'qux')]
    will result in the command
      foo=bar;baz=qux!
    :param command_tuples: a list of key-value pairs, e.g. ('username', 'foo')
    '''
    command_list = []
    for (key, val) in command_tuples:
        command_list.append(packets.FIELD_SEPARATOR.join([key, str(val)]))
    return (packets.COMMAND_SEPARATOR.
            join([command for command in command_list])) + terminator


def _assemble_blink1_command(command_tuples):
    '''
    Assemble a list of command tuples into a valid packet. Due to backwards
    compatibility (due to the prior existence of _assemble_command(...))
    this method only acts on the first ON item in the list. By still allowing
    a list, one can potentially extend this in future to allow for compound
    states, e.g. a blink(1) device with multiple RGB LEDs, or using a
    transition among colours when there's only a single RGB LED.
    '''
    # We only have one LED (at index 0)
    led_number = 0
    # 1 second divided by 10
    fade_millis = 1000 / 10
    th = (fade_millis & 0xff00) >> 8
    tl = fade_millis & 0x00ff
    # We assume we will always get at least one ON state.
    # No way to treat the SOS state yet, other than ON.
    color = [t[0] for t in command_tuples
             if t[1] in [led_states.ON, led_states.SOS]][0]
    if color == fields.GREEN_LED:
        red = 0
        green = 255
        blue = 0
    elif color == fields.RED_LED:
        red = 255
        green = 0
        blue = 0
    elif color == fields.BLUE_LED:
        red = 0
        green = 0
        blue = 255
    elif color == fields.YELLOW_LED:
        red = 255
        green = 150
        blue = 0
    # 0x63 = 'c' => fade to RGB
    # 0x6E = 'n' => set to RGB
    return [0x01, 0x63, red, green, blue, th, tl, led_number]


def _assemble_led_command(led_field, led_state):
    '''
    Assemble a LED command, e.g.
      red=on\n
    :param led_field: the LED
    :param led_state: the LED's status
    '''
    return _assemble_command({(led_field, led_state)}, packets.ALT_TERMINATOR)


def get_challenge_request():
    '''
    Get the request to challenge the USB device with.
    http://en.wikipedia.org/wiki/Blinkenlights
    '''
    return packets.CHALLENGE_REQUEST + packets.ALT_TERMINATOR


def is_challenge_response(data):
    '''
    Check if the challenge response received from the USB device is valid.
    :param data: the raw data
    '''
    return utils.strip(data) == packets.CHALLENGE_RESPONSE
