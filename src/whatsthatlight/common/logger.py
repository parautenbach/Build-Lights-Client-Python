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
import logging.config
import os.path


class InvalidLoggerConfigException(Exception):
    '''
    Exception raised when an invalid config was specified.
    '''

    def __init__(self, message):
        '''
        Constructor.
        :param message: the message explaining the exception
        '''
        self.message = message


def get_logger(conf_path):
    '''
    Initialise the logger from a config file.
    :param conf_path: Path to the logger's config file.
    '''
    if not os.path.exists(conf_path):
        raise InvalidLoggerConfigException('Cannot find logger configuration')
    logging.config.fileConfig(conf_path)
    logger = logging.getLogger()
    return logger
