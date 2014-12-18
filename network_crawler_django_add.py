import netmiko
from cdp_automation.cdp_functions import *
from net_system.models import NetworkDevice, Credentials, SnmpCredentials
import django
from paramiko import AuthenticationException
from socket import gaierror


django.setup()

root_node = NetworkDevice.objects.all()[0]
nfcu_creds = Credentials.objects.all()[0]
SSHClass = netmiko.ssh_dispatcher('cisco_nxos')

ssh = SSHClass(ip=root_node.device_name, username=root_node.credentials.username, password=root_node.credentials.password)
saved, failed, visited = [], [], []

saved.append(root_node.device_name)

print 'Crawling the root node...'
while (len(saved) > 0) and (saved[0] not in visited):
    try:
        print 'connecting to {}'.format(saved[0])
        ssh = SSHClass(ip=saved[0], username=nfcu_creds.username, password=nfcu_creds.password)
        ver_check, cdp_ = ssh.send_command('show version'), ssh.send_command('show cdp neigh det')

    except (AuthenticationException, gaierror) as e:
        failed.append(saved[0])
        print "failed to connect to {} due to {}".format(saved[0], e)
        continue


    if 'Cisco Nexus Operating' in ver_check:
        neighbors = nexus_cdp_parser(cdp_)
    else:
        neighbors = ios_cdp_parser(cdp_)

    neighbors_set = set([dev['dev_name'] for dev in neighbors.itervalues()])
    neighbors_data = [dev for dev in neighbors.itervalues()]

    print "{} has a total of {} neihbors".format(saved[0], len(neighbors_data))
    print
    print "*" * 80
    print 
    print

    ssh.disconnect()
    visited.append(saved[0])
    saved.pop(0)

    for counter, neigh in enumerate(neighbors_data):
        print "processing device {}/{}...".format(counter, len(neighbors_data))
        if neigh['dev_name'] in (saved or failed):
            print "{} already saved or failed".format(neigh['dev_name'])
            continue
        try:
            print 'trying to see if {} is reachable...'.format(neigh['dev_name'])
            try_ssh = SSHClass(ip=neigh['dev_name'], username=nfcu_creds.username, password=nfcu_creds.password)

        except (AuthenticationException, gaierror) as e:
            failed.append(neigh['dev_name'])
            print "failed to connect to {} due to {}".format(neigh['dev_name'], e)
            continue

        try_ssh.disconnect()
        if 'Eth' in neigh['remote_intf']:
            dev_class = 'cisco_nxos_ssh'

        else:
            dev_class = 'cisco_ios_ssh' 

        device = NetworkDevice(
            device_name = neigh['dev_name'], 
            ip_address = neigh['ip_addr'], 
            credentials = nfcu_creds, 
            ssh_port = 22, 
            vendor = 'Cisco', 
            model = neigh['model'],
            device_class = dev_class,
             )

        try:
            device.save()
        except IntegrityError as e:
            print 'Failed to save device {}...due to {}'.format(neigh['dev_name'], e)
            failed.append(neigh['dev_name'])
            continue

        print "saved {}, on to the next!".format(neigh['dev_name'])
        saved.append(neigh['dev_name'])













    


