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
import ConfigParser
import unittest

# Local imports
from whatsthatlight.common import config


class Test(unittest.TestCase):
    '''
    Test the config module.
    '''

    def test_get_logger_conf_path(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = 'whatsthatlight/logger.conf'
        actual = the_config.get_logger_conf_path()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        config_parser.add_section(config.LOGGER_SECTION)
        expected = 'foo'
        config_parser.set(config.LOGGER_SECTION,
                          config.LOGGER_CONFIG_OPTION,
                          expected)
        the_config = config.Config(config_parser)
        actual = the_config.get_logger_conf_path()
        self.assertEqual(actual, expected)

    def test_get_client_address_and_port(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = ('127.0.0.1', 9192)
        actual = the_config.get_client_address_and_port()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        expected = ('1.2.3.4', 56789)
        config_parser.add_section(config.CLIENT_SECTION)
        config_parser.set(config.CLIENT_SECTION,
                          config.CLIENT_ADDRESS_OPTION,
                          expected[0])
        config_parser.set(config.CLIENT_SECTION,
                          config.CLIENT_PORT_OPTION,
                          str(expected[1]))
        the_config = config.Config(config_parser)
        actual = the_config.get_client_address_and_port()
        self.assertEqual(actual, expected)

    def test_get_server_address_and_port(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = ('ci', 9191)
        actual = the_config.get_server_address_and_port()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        expected = ('2.3.4.5', 45678)
        config_parser.add_section(config.SERVER_SECTION)
        config_parser.set(config.SERVER_SECTION,
                          config.SERVER_ADDRESS_OPTION,
                          expected[0])
        config_parser.set(config.SERVER_SECTION,
                          config.SERVER_PORT_OPTION,
                          str(expected[1]))
        the_config = config.Config(config_parser)
        actual = the_config.get_server_address_and_port()
        self.assertEqual(actual, expected)

    def test_get_vendor_and_product_ids(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = (0x16c0, 0x0486)
        actual = the_config.get_vendor_and_product_ids()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        expected = (0x1a2b, 0x3c4d)
        config_parser.add_section(config.DEVICE_SECTION)
        config_parser.set(config.DEVICE_SECTION,
                          config.DEVICE_VENDOR_ID_OPTION,
                          '%0#6x' % expected[0])
        config_parser.set(config.DEVICE_SECTION,
                          config.DEVICE_PRODUCT_ID_OPTION,
                          '%0#6x' % expected[1])
        the_config = config.Config(config_parser)
        actual = the_config.get_vendor_and_product_ids()
        self.assertEqual(actual, expected)

    def test_get_interface_number(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = 1
        actual = the_config.get_interface_number()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        expected = 5
        config_parser.add_section(config.DEVICE_SECTION)
        config_parser.set(config.DEVICE_SECTION,
                          config.DEVICE_INTERFACE_NUMBER_OPTION,
                          str(expected))
        the_config = config.Config(config_parser)
        actual = the_config.get_interface_number()
        self.assertEqual(actual, expected)

    def test_get_username(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = ''
        actual = the_config.get_username()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        config_parser.add_section(config.CLIENT_SECTION)
        expected = 'foo'
        config_parser.set(config.CLIENT_SECTION,
                          config.CLIENT_USERNAME_OPTION,
                          expected)
        the_config = config.Config(config_parser)
        actual = the_config.get_username()
        self.assertEqual(actual, expected)

    def test_get_usage_and_usage_page(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = (0xffc9, 0x0004)
        actual = the_config.get_usage_and_usage_page()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        expected = (0x3c4d, 0x1a2b)
        config_parser.add_section(config.DEVICE_SECTION)
        config_parser.set(config.DEVICE_SECTION,
                          config.DEVICE_USAGE_PAGE_OPTION,
                          '%0#6x' % expected[0])
        config_parser.set(config.DEVICE_SECTION,
                          config.DEVICE_USAGE_OPTION,
                          '%0#6x' % expected[1])
        the_config = config.Config(config_parser)
        actual = the_config.get_usage_and_usage_page()
        self.assertEqual(actual, expected)

    def test_get_device_class(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = 'PyUsbDevice'
        actual = the_config.get_device_class()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        config_parser.add_section(config.DEVICE_SECTION)
        expected = 'foo'
        config_parser.set(config.DEVICE_SECTION,
                          config.DEVICE_CLASS_OPTION,
                          expected)
        the_config = config.Config(config_parser)
        actual = the_config.get_device_class()
        self.assertEqual(actual, expected)

    def test_get_usb_protocol(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = 'DasBlinkenLichten'
        actual = the_config.get_usb_protocol()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        config_parser.add_section(config.DEVICE_SECTION)
        expected = 'BlinkFoo'
        config_parser.set(config.DEVICE_SECTION,
                          config.DEVICE_USB_PROTOCOL_OPTION,
                          expected)
        the_config = config.Config(config_parser)
        actual = the_config.get_usb_protocol()
        self.assertEqual(actual, expected)

    def test_get_usb_transfer_mode(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = 'Raw'
        actual = the_config.get_usb_transfer_mode()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        config_parser.add_section(config.DEVICE_SECTION)
        expected = 'ControlFoo'
        config_parser.set(config.DEVICE_SECTION,
                          config.DEVICE_USB_TRANSFER_OPTION,
                          expected)
        the_config = config.Config(config_parser)
        actual = the_config.get_usb_transfer_mode()
        self.assertEqual(actual, expected)

    def test_get_device_monitor_class(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = 'PyUdevDeviceMonitor'
        actual = the_config.get_device_monitor_class()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        config_parser.add_section(config.MONITOR_SECTION)
        expected = 'foo'
        config_parser.set(config.MONITOR_SECTION,
                          config.MONITOR_CLASS_OPTION,
                          expected)
        the_config = config.Config(config_parser)
        actual = the_config.get_device_monitor_class()
        self.assertEqual(actual, expected)

    def test_get_polling_device_monitor_period(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = 1
        actual = the_config.get_polling_device_monitor_period()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        config_parser.add_section(config.MONITOR_SECTION)
        expected = 3
        config_parser.set(config.MONITOR_SECTION,
                          config.MONITOR_POLLING_PERIOD_OPTION,
                          str(expected))
        the_config = config.Config(config_parser)
        actual = the_config.get_polling_device_monitor_period()
        self.assertEqual(actual, expected)

    def test_get_registration_retry_period(self):
        '''
        Retrieve the default, followed by retrieving the configured value.
        '''
        # Create an empty config
        config_parser = ConfigParser.SafeConfigParser()
        the_config = config.Config(config_parser)

        # Test that we get the default
        expected = 5
        actual = the_config.get_registration_retry_period()
        self.assertEqual(actual, expected)

        # Test that we get the configured value
        config_parser.add_section(config.CLIENT_SECTION)
        expected = 10
        config_parser.set(config.CLIENT_SECTION,
                          config.CLIENT_REGISTRATION_RETRY_PERIOD_OPTION,
                          str(expected))
        the_config = config.Config(config_parser)
        actual = the_config.get_registration_retry_period()
        self.assertEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()
