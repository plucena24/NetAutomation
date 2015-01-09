import netmiko
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException
from cdp_automation.cdp_functions import *
from net_system.models import NetworkDevice, Credentials, SnmpCredentials
import django
from paramiko import AuthenticationException, SSHException
from socket import gaierror
from collections import defaultdict
import multiprocessing.dummy


### Used to fix Django setup issue ###
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
### Used to fix Django setup issue ###


# log into vna1er1-wan and parse bgp rib
# we are looking for all /32 routes that end in .8
# these are the Anira loopbacks on each branch router
# from this loopback we will figure out the branch subnet
# and derrive the branch router, switch, and firewall.

def find_os_version(output):
    '''
    String in show version will be similar to the following:
    Cisco IOS Software, IOS-XE Software (PPC_LINUX_IOSD-ADVENTERPRISEK9-M), Version 15.2(4)S4, RELEASE SOFTWARE (fc1)
    Hardware:   ASA5505, 512 MB RAM, CPU Geode 500 MHz
    '''

    match = re.search(r'Cisco IOS Software, (.*)',output)
    if match:
        return match.group(1)

    match = re.search(r'Cisco Adaptive Security Appliance Software Version (.*)', output)
    if match:

        return match.group(1)
    else:
        return None  


def find_serial_number(output):
    '''
    String in show version will be similar to the following:
    Processor board ID FTX10000001
    Serial Number: JMX172940K0
    '''

    match = re.search(r'Processor board ID (.*)', output)
    if match:
        return match.group(1)

    match = re.search(r'Serial Number: (.*)', output)
    if match:
        return match.group(1)

    else:
        return None

def find_model(output):
    '''
    String in show version will be similar to the following:
    Cisco CISCO2921/K9 (revision 1.0) with 1007584K/40960K bytes of memory.
    Hardware:   ASA5505, 512 MB RAM, CPU Geode 500 MHz
    '''

    match = re.search(r'.*bytes of memory', output)
    if match:
        return match.group().split()[1]

    match = re.search(r'Hardware:\s+(.*?),', output)
    if match:      
        return match.group(1)

    else:
        return None


def find_device_name(output):
    '''
    String in show version will be similar to the following:
    ASA-CRNCA up 59 days 6 hours
    RTR-CRNCA uptime is 17 weeks, 5 days, 3 hours, 58 minutes
    '''

    match = re.search(r'(.*) uptime is ', output)
    if match:
        return match.group(1)

    match = re.search(r'(.*) up ', output)
    if match:
        return match.group(1)
    else:
        return None


def crawl_branch_wan(device):
  
    class_mapper = {
    '26' : 'cisco_asa', 
    '5'  : 'cisco_ios',
    '30' : 'cisco_ios',
    }

    SSHClient = netmiko.ssh_dispatcher(class_mapper[device.split('.')[-1]])

    try:
        print 'connecting to {}'.format(device)
        ssh = SSHClient(ip=device, username=creds.username, password=creds.password, secret=creds.password)      
    except (AuthenticationException, gaierror, SSHException, NetMikoAuthenticationException, NetMikoTimeoutException, ValueError) as e:
        print 'Failed to connect to {} due to {}'.format(device, e)
        return False

    output = ssh.send_command("show version", delay_factor=3)

    serial = find_serial_number(output)
    version = find_os_version(output)
    name = find_device_name(output)
    model = find_model(output)


    new_dev = NetworkDevice(
    device_name = name, 
    ip_address = device, 
    credentials = creds, 
    ssh_port = 22, 
    vendor = 'Cisco', 
    model = model,
    device_class = class_mapper[device.split('.')[-1]]+'_ssh',
    domain = 'nfcu.net',
    serial_number = serial,
    os_version = version,
     )

    try:
        new_dev.save()
    except django.db.utils.IntegrityError as e:
        print "The following device does NOT have a name {}".format(device)

    print name, device, model, serial, version 

    return True



if __name__ == '__main__':

    django.setup()


    prefix_re = re.compile(r'(\d+\.\d+\.\d+\.\d+/32)')

    net_device = NetworkDevice.objects.get(device_name='VNA1ER1-WAN')
    device_class, device_name, device_ip, device_username, device_password = net_device.device_class, net_device.device_name, \
    net_device.ip_address, net_device.credentials.username, net_device.credentials.password

    # even though we already have the creds, we need to import this 
    # django object so that we can save it on each device
    creds = Credentials.objects.get(id=1)

    SSHClient = netmiko.ssh_dispatcher(device_type=device_class[:-4])
    ssh = SSHClient(ip=device_name, username=device_username, password=device_password)
    output = ssh.send_command("show ip bgp | inc .8/32")
    outlines = output.splitlines()

    # grab the prefix from the show bgp output
    base_prefixes = [prefix_re.search(line).group(1) for line in outlines]

    # remove the /32 from the preifx and split each prefix on the dot 
    # to perform operations on each octet later
    all_nodes = [prefix[:-3].split('.') for prefix in base_prefixes]
    #dev_dict = defaultdict(list)

    dev_list = []

    for branch in all_nodes:
        # all branch routers are .5
        branch[-1] = '5'
        dev_list.append('.'.join(branch))

        # all firewalls are .26
        branch[-1] = '26'
        dev_list.append('.'.join(branch))

        # all branch switches are .30 on the 1st subnet of the /23
        branch[-1] = '30'
        branch[-2] = str(int(branch[-2])-1)
        dev_list.append('.'.join(branch))


    pool = multiprocessing.dummy.Pool(processes=24)

    pool_results = [pool.apply_async(crawl_branch_wan, args=(dev,)) for dev in dev_list]

    pool.close()
    pool.join()

    for result in pool_results:
        print result.get()

