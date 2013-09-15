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

# Client section
CLIENT_SECTION = 'client'
CLIENT_ADDRESS_OPTION = 'address'
CLIENT_ADDRESS_DEFAULT = '127.0.0.1'
CLIENT_PORT_OPTION = 'port'
CLIENT_PORT_DEFAULT = 9192
CLIENT_USERNAME_OPTION = 'username'
CLIENT_USERNAME_DEFAULT = ''
CLIENT_REGISTRATION_RETRY_PERIOD_OPTION = 'registration_retry_period'
CLIENT_REGISTRATION_RETRY_PERIOD_DEFAULT = 5

# Server section
SERVER_SECTION = 'server'
SERVER_ADDRESS_OPTION = CLIENT_ADDRESS_OPTION
SERVER_ADDRESS_DEFAULT = 'ci'
SERVER_PORT_OPTION = CLIENT_PORT_OPTION
SERVER_PORT_DEFAULT = 9191

# Device section
DEVICE_SECTION = 'device'
DEVICE_VENDOR_ID_OPTION = 'vendor_id'
DEVICE_VENDOR_ID_DEFAULT = 0x16c0
DEVICE_PRODUCT_ID_OPTION = 'product_id'
DEVICE_PRODUCT_ID_DEFAULT = 0x0486
DEVICE_INTERFACE_NUMBER_OPTION = 'interface_number'
DEVICE_INTERFACE_NUMBER_DEFAULT = 1
DEVICE_USAGE_PAGE_OPTION = 'usage_page'
DEVICE_USAGE_PAGE_DEFAULT = 0xffc9
DEVICE_USAGE_OPTION = 'usage'
DEVICE_USAGE_DEFAULT = 0x0004
DEVICE_CLASS_OPTION = 'class'
DEVICE_CLASS_DEFAULT = 'PyUsbDevice'
DEVICE_USB_PROTOCOL_OPTION = 'usb_protocol'
DEVICE_USB_PROTOCOL_DEFAULT = 'DasBlinkenLichten'
DEVICE_USB_TRANSFER_OPTION = 'usb_transfer_mode'
DEVICE_USB_TRANSFER_DEFAULT = 'Raw'

# Monitor section
MONITOR_SECTION = 'monitor'
MONITOR_CLASS_OPTION = 'class'
MONITOR_CLASS_DEFAULT = 'PyUdevDeviceMonitor'
MONITOR_POLLING_PERIOD_OPTION = 'polling_period'
MONITOR_POLLING_PERIOD_DEFAULT = 1

# Logger section
LOGGER_SECTION = 'logger'
LOGGER_CONFIG_OPTION = 'config'
LOGGER_CONFIG_DEFAULT = 'whatsthatlight/logger.conf'


class Config:
    '''
    Configuration class.
    '''

    def __init__(self, _config_parser):
        '''
        Constructor.
        :param _config_parser: An initialised Python ConfigParser.
        '''
        self._config_parser = _config_parser

    def get_usb_protocol(self):
        '''
        Get the USB protocol to use with the device.
        '''
        return self._get_string(DEVICE_SECTION,
                                DEVICE_USB_PROTOCOL_OPTION,
                                DEVICE_USB_PROTOCOL_DEFAULT)

    def get_usb_transfer_mode(self):
        '''
        Get the USB transfer mode to use with the device.
        '''
        return self._get_string(DEVICE_SECTION,
                                DEVICE_USB_TRANSFER_OPTION,
                                DEVICE_USB_TRANSFER_DEFAULT)

    def get_logger_conf_path(self):
        '''
        Get the path to the logger's config file.
        '''
        return self._get_string(LOGGER_SECTION,
                                LOGGER_CONFIG_OPTION,
                                LOGGER_CONFIG_DEFAULT)

    def get_client_address_and_port(self):
        '''
        Get the (address, port) tuple for the client's listener.
        '''
        address = (CLIENT_SECTION,
                   CLIENT_ADDRESS_OPTION,
                   CLIENT_ADDRESS_DEFAULT)
        port = (CLIENT_SECTION,
                CLIENT_PORT_OPTION,
                CLIENT_PORT_DEFAULT)
        return self._get_string_int_tuple(address, port)

    def get_server_address_and_port(self):
        '''
        Get the (address, port) tuple for the server's listener.
        '''
        address = (SERVER_SECTION,
                   SERVER_ADDRESS_OPTION,
                   SERVER_ADDRESS_DEFAULT)
        port = (SERVER_SECTION,
                SERVER_PORT_OPTION,
                SERVER_PORT_DEFAULT)
        return self._get_string_int_tuple(address, port)

    def get_vendor_and_product_ids(self):
        '''
        Get the (vid, pid) tuple for the device.
        '''
        vendor_id = (DEVICE_SECTION,
                     DEVICE_VENDOR_ID_OPTION,
                     DEVICE_VENDOR_ID_DEFAULT)
        product_id = (DEVICE_SECTION,
                      DEVICE_PRODUCT_ID_OPTION,
                      DEVICE_PRODUCT_ID_DEFAULT)
        return self._get_four_digit_hex_tuple_pair(vendor_id, product_id)

    def get_usage_and_usage_page(self):
        '''
        Get the (usage_page, usage) tuple for the device.
        '''
        usage_page = (DEVICE_SECTION,
                      DEVICE_USAGE_PAGE_OPTION,
                      DEVICE_USAGE_PAGE_DEFAULT)
        usage = (DEVICE_SECTION,
                 DEVICE_USAGE_OPTION,
                 DEVICE_USAGE_DEFAULT)
        return self._get_four_digit_hex_tuple_pair(usage_page, usage)

    def get_interface_number(self):
        '''
        Get the interface number for a PyUSB device.
        '''
        return self._get_int(DEVICE_SECTION,
                             DEVICE_INTERFACE_NUMBER_OPTION,
                             DEVICE_INTERFACE_NUMBER_DEFAULT)

    def get_username(self):
        '''
        Get the username representing the user.
        '''
        return self._get_string(CLIENT_SECTION,
                                CLIENT_USERNAME_OPTION,
                                CLIENT_USERNAME_DEFAULT)

    def get_device_class(self):
        '''
        Get the device class to use.
        '''
        return self._get_string(DEVICE_SECTION,
                                DEVICE_CLASS_OPTION,
                                DEVICE_CLASS_DEFAULT)

    def get_device_monitor_class(self):
        '''
        Get the device monitor class to use.
        '''
        return self._get_string(MONITOR_SECTION,
                                MONITOR_CLASS_OPTION,
                                MONITOR_CLASS_DEFAULT)

    def get_polling_device_monitor_period(self):
        '''
        Get the polling period when monitoring a device via polling.
        '''
        return self._get_int(MONITOR_SECTION,
                             MONITOR_POLLING_PERIOD_OPTION,
                             MONITOR_POLLING_PERIOD_DEFAULT)

    def get_registration_retry_period(self):
        '''
        Get the registration retry period when registering with the
        notification server failed.
        '''
        return self._get_int(CLIENT_SECTION,
                             CLIENT_REGISTRATION_RETRY_PERIOD_OPTION,
                             CLIENT_REGISTRATION_RETRY_PERIOD_DEFAULT)

    def _get_int(self, section, option, default):
        '''
        Get an int.
        :param section: the section
        :param option: the option (key)
        :param default: the default value for the key or value fails to parse
        '''
        try:
            return self._config_parser.getint(section, option)
        except:
            return default

    def _get_string(self, section, option, default):
        '''
        Get the string value.
        :param section: the section
        :param option: the option (key)
        :param default: the default value for the key or value fails to parse
        '''
        try:
            return self._config_parser.get(section, option)
        except:
            return default

    def _get_string_int_tuple(self, string_part, int_part):
        '''
        Get the (string, int) tuple.
        :param string_part: a (section, option, default) tuple
        :param int_part: a (section, option, default) tuple
        '''
        try:
            address = self._config_parser.get(string_part[0],
                                              string_part[1])
            port = self._config_parser.getint(int_part[0],
                                              int_part[1])
            return (address, port)
        except:
            return (string_part[2], int_part[2])

    def _get_four_digit_hex_tuple_pair(self, tuple1, tuple2):
        '''
        Get a (hex, hex) tuple.
        :param tuple1: a (section, option, default) tuple
        :param tuple2: a (section, option, default) tuple
        '''
        try:
            hex1 = int(self._config_parser.get(tuple1[0], tuple1[1]), 16)
            hex2 = int(self._config_parser.get(tuple2[0], tuple2[1]), 16)
            return (hex1, hex2)
        except:
            return (tuple1[2], tuple2[2])
