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
import request_types


class InvalidRequestException(Exception):
    '''
    Exception raised when an request is invalid.
    '''

    def __init__(self, message):
        '''
        Constructor.
        :param message: the message explaining the exception
        '''
        self.message = message


class BaseRequest(object):
    '''
    A base request.
    '''

    def __init__(self):
        '''
        Constructor.
        '''
        # Override this in sub classes
        self._type = request_types.UNKNOWN

    def get_type(self):
        '''
        Get the request's type.
        '''
        return self._type


class RegistrationRequest(BaseRequest):
    '''
    A registration request for registering a user with the notification server.
    '''

    def __init__(self, hostname, username):
        '''
        Constructor.
        :param hostname: the user's host
        :param username: the user's username
        '''
        super(type(self), self).__init__()
        self._type = request_types.REGISTER
        self._hostname = hostname
        self._username = username

    def get_hostname(self):
        '''
        The host to be registered.
        '''
        return self._hostname

    def get_username(self):
        '''
        The user to be registered.
        '''
        return self._username


class BuildActiveRequest(BaseRequest):
    '''
    A request to indicate whether any builds are active.
    '''

    def __init__(self, is_build_active):
        '''
        Constructor.
        :param is_build_active: true if a build is active
        '''
        super(type(self), self).__init__()
        self._type = request_types.BUILD_ACTIVE
        self._is_build_active = is_build_active

    def is_build_active(self):
        '''
        Return true if a build is active.
        '''
        return self._is_build_active


class AttentionRequest(BaseRequest):
    '''
    A request to indicate whether and what type of attention is required.
    '''

    def __init__(self, attention, priority):
        '''
        Constructor.
        :param attention: true if attention is required
        :param priority: true if attention is priority
        '''
        super(type(self), self).__init__()
        self._type = request_types.ATTENTION
        self._attention = attention
        if priority and not attention:
            raise InvalidRequestException('Priority only valid if '
                                          'attention is required.')
        self._priority = priority

    def is_required(self):
        '''
        Return true if attention is required.
        '''
        return self._attention

    def is_priority(self):
        '''
        Return true if attention is priority.
        '''
        return self._priority


class StatusRequest(BaseRequest):
    '''
    A request to indicate whether the status of
    a client or server is up or down.
    '''

    def __init__(self, status):
        '''
        Constructor.
        :param is_build_active: true if a build is active
        '''
        super(type(self), self).__init__()
        self._type = request_types.SERVER_STATUS
        self._status = status

    def is_up(self):
        '''
        Return true if the client or server is up.
        '''
        return self._status
