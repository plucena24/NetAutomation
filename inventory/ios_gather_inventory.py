import re
from general_functions import parse_uptime

class IosGatherInventory(object):
    '''
    Base Class for Cisco IOS and IOS-XE devices
    '''

    def __init__(self, net_device, output):
        self.net_device = net_device
        self.output = output     


    def find_os_version(self):
        '''
        String in show version will be similar to the following:
        Cisco IOS Software, IOS-XE Software (PPC_LINUX_IOSD-ADVENTERPRISEK9-M), Version 15.2(4)S4, RELEASE SOFTWARE (fc1)
        '''

        match = re.search(r'Cisco IOS Software, (.*)', self.output)
        if match:
            self.net_device.os_version = match.group(1)
            print self.net_device.os_version
            self.net_device.save()

    def find_serial_number(self):
        '''
        String in show version will be similar to the following:
        Processor board ID FTX10000001
        '''

        match = re.search(r'Processor board ID (.*)', self.output)
        if match:
            self.net_device.serial_number = match.group(1)
            print self.net_device.serial_number
            self.net_device.save()

    def find_uptime(self):
        '''
        String in show version will be similar to the following:
        hostname uptime is 8 weeks, 2 days, 23 hours, 22 minutes
        '''

        match = re.search(r'uptime is (.*)', self.output)
        if match:
            time_str = match.group(1)
            self.net_device.uptime_seconds = parse_uptime(time_str)
            print self.net_device.uptime_seconds
            self.net_device.save()


if __name__ == '__main__':
    import netmiko
    import django
    from net_system.models import NetworkDevice

    django.setup()

    devices = NetworkDevice.objects.filter(device_name = 'VNA1DS1-WAN')

    for device in devices:

        SSHClass = netmiko.ssh_dispatcher(str(device.device_class)[:-4])

        ssh = SSHClass(ip=device.ip_address, username=device.credentials.username, password=device.credentials.password)

        output = ssh.send_command('show version')

        inventory = IosGatherInventory(device, output)

        inventory.find_os_version()
        inventory.find_serial_number()
        inventory.find_uptime()