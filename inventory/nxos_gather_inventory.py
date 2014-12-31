import xmltodict
from general_functions import parse_uptime

class NexusGatherInventory(object):
    '''
    Base Class for Nexus Devices. Takes in a NetworkDevice object
    from the django databse along with xml output from the device
    '''

    def __init__(self, net_device, output):
        self.net_device = net_device
        self.output = output
        self.prepare_xml_output()


    def prepare_xml_output(self):
        xml = xmltodict.parse(self.output)
        try:
            self.xml_data = xml[u'nf:rpc-reply'][u'nf:data'][u'show'][u'version'][u'__XML__OPT_Cmd_sysmgr_show_version___readonly__'][u'__readonly__']
        except IndexError as e:
            print "XML Data Parsing Error"


    def find_os_version(self):
        '''
        Parses the XML dict for the OS Version
        '''
        self.net_device.os_version = str(self.xml_data[u'sys_ver_str'])
        print self.net_device.os_version
        self.net_device.save()

    def find_serial_number(self):
        '''
        String in show version will be similar to the following:
        Processor board ID FTX10000001
        '''
        self.net_device.serial_number = str(self.xml_data[u'proc_board_id'])
        print self.net_device.serial_number
        self.net_device.save()

    def find_uptime(self):
        '''
        Nexus uptime string only uses days, hours, and minutes. The IOS equivalent
        uses years, and weeks. 
        '''
        days = str(self.xml_data[u'kern_uptm_days'])
        hours = str(self.xml_data[u'kern_uptm_hrs'])
        minutes = str(self.xml_data[u'kern_uptm_mins'])

        self.uptime_list = [days, hours, minutes] 
        self.uptime_str = "{} days, {} hours, {} minutes".format(*self.uptime_list)
        self.net_device.uptime_seconds = parse_uptime(self.uptime_str)
        print self.net_device.uptime_seconds
        self.net_device.save()

if __name__ == '__main__':
    import netmiko
    import django
    from net_system.models import NetworkDevice

    django.setup()

    devices = NetworkDevice.objects.filter(device_name = 'VNA1DS1-SF')

    for device in devices:

        SSHClass = netmiko.ssh_dispatcher(str(device.device_class)[:-4])

        ssh = SSHClass(ip=device.ip_address, username=device.credentials.username, password=device.credentials.password)

        output = ssh.send_command('show version | xml | exclude "]]>]]>"')

        inventory = NexusGatherInventory(device, output)

        inventory.find_os_version()
        inventory.find_serial_number()
        inventory.find_uptime()




