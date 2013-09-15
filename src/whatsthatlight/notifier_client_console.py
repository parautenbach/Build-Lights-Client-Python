#!/usr/bin/python
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
import signal
import threading
import sys

# Local imports
import notifier_client
from common import argument_parser
from common import config
from common import logger
from common import usb_protocol_types
from common import usb_transfer_types
from device_controller import DeviceController


def stop_handler(_signum, _frame):
    '''
    A handler to stop the client.
    :param _signum: Ignored
    :param _frame: Ignored
    '''
    global client, event
    client.stop()
    event.set()


def main():
    '''
    Main application.
    '''
    global client, event

    # Create a client and set signal handlers to stop the client
    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    # Create and event used to keep this script alive while running the client
    event = threading.Event()
    event.clear()

    # Load the application configuration,
    # initialise logging and create the client
    args = argument_parser.get_arguments()
    config_parser = ConfigParser.SafeConfigParser()
    try:
        config_parser.readfp(open(args.config))
    except IOError, e:
        print('Invalid config file: {0}'.format(args.config))
        print('{0} ({1})'.format(e.strerror, e.errno))
        exit(1)
    the_config = config.Config(config_parser)
    the_logger = logger.get_logger(the_config.get_logger_conf_path())

    # Pick a USB device class
    (vendor_id, product_id) = the_config.get_vendor_and_product_ids()
    device_class = the_config.get_device_class()
    if device_class == 'PyUsbDevice':
        from devices import PyUsbDevice
        interface_number = the_config.get_interface_number()
        device = PyUsbDevice(vendor_id,
                             product_id,
                             interface_number)
    elif device_class == 'TeensyDevice':
        from devices import TeensyDevice
        (usage_page, usage) = the_config.get_usage_and_usage_page()
        device = TeensyDevice(vendor_id, product_id, usage_page, usage)
    elif device_class == 'Blink1Device':
        from devices import Blink1Device
        interface_number = the_config.get_interface_number()
        device = Blink1Device(vendor_id, product_id, interface_number)
    else:
        raise Exception('Invalid or device class not supported: {0}'.
                        format(device_class))

    # Pick a monitor class
    device_monitor_class = the_config.get_device_monitor_class()
    if device_monitor_class == 'PyUdevDeviceMonitor':
        import pyudev
        from device_monitors import PyUdevDeviceMonitor
        monitor = PyUdevDeviceMonitor(vendor_id,
                                      product_id,
                                      pyudev,
                                      logger=the_logger)
    elif device_monitor_class == 'PollingDeviceMonitor':
        from device_monitors import PollingDeviceMonitor
        monitor_polling_period = the_config.get_polling_device_monitor_period()
        monitor = PollingDeviceMonitor(device,
                                       polling_interval=monitor_polling_period,
                                       logger=the_logger)
    else:
        raise Exception('Invalid or monitor class not supported: {0}'.
                        format(device_monitor_class))

    # Pick a USB protocol
    usb_protocol = the_config.get_usb_protocol()
    if usb_protocol == 'DasBlinkenLichten':
        upt = usb_protocol_types.DAS_BLINKENLICHTEN
    elif usb_protocol == 'Blink1':
        upt = usb_protocol_types.BLINK1
    else:
        raise Exception('Invalid or USB protocol not supported: {0}'.
                        format(usb_protocol))

    # Pick a USB transfer type (RAW or CTRL)
    usb_transfer_mode = the_config.get_usb_transfer_mode()
    if usb_transfer_mode == 'Raw':
        usb_transfer_type = usb_transfer_types.RAW
    elif usb_transfer_mode == 'Control':
        usb_transfer_type = usb_transfer_types.CONTROL
    else:
        raise Exception('Invalid or USB control transfer mode '
                        'not supported: {0}'.
                        format(usb_transfer_mode))

    # Assemble the client
    (client_address, client_port) = the_config.get_client_address_and_port()
    (server_address, server_port) = the_config.get_server_address_and_port()
    username = the_config.get_username()
    retry_period = the_config.get_registration_retry_period()
    controller = DeviceController(device,
                                  usb_transfer_type,
                                  monitor,
                                  logger=the_logger)
    client = notifier_client.NotifierClient(username,
                                            controller,
                                            address=client_address,
                                            port=client_port,
                                            server_address=server_address,
                                            server_port=server_port,
                                            retry_period=retry_period,
                                            usb_protocol_type=upt,
                                            logger=the_logger)

    # Run as long as the client is running
    client.start()
    while client.running:
        event.wait(5)
    sys.exit()

if __name__ == '__main__':
    main()
