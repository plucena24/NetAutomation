import netmiko
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException
from cdp_automation.cdp_functions import *
from net_system.models import NetworkDevice, Credentials, SnmpCredentials
import django
from paramiko import AuthenticationException, SSHException
from socket import gaierror


# start django so that all the models can be imported
django.setup()

# a single node has been manually saved onto the DB.
# this is the root node from which all other nodes will be discovered.

root_node = NetworkDevice.objects.get(device_name='ROUTER1')
creds = Credentials.objects.get(pk=1)

# this node is NX-OS
SSHClass = netmiko.ssh_dispatcher('cisco_nxos')
ssh = SSHClass(ip=root_node.device_name, username=root_node.credentials.username, password=root_node.credentials.password)

# set up the lists to be used as counters
# saved is our Queue 
# visited keeps track of all devices that we have "crawled" - ie, looked at its CDP neighbors
# All of the valid CDP neighbors are added to the Queue
saved, failed, visited = [], [], []

# add the root node to the Queue - it will be processed first
saved.append(root_node.device_name)

print 'Crawling the root node...'

# we will process until the Queue is empty
while (len(saved) > 0):

    # if the node has already been visited then we move on to the next 
    # and remove it from the Queue
    if saved[0] in visited:
        print '{} device has already been visited'.format(saved[0])
        saved.pop(0)
        continue
    
    # dont scan the NetApps! 
    if saved[0].startswith('NA-'):
        print '{} device is a NetApp - Skip'.format(saved[0])
        saved.pop(0)
        continue

    print '#' * 80
    print 
    print
    # print the len of the Queue during each pass
    # this will show the progress being made on the Queue
    print len(saved)
    print 
    print
    print '#' * 80
    try:
        print 'connecting to {}'.format(saved[0])
        # connect to the device being processing from the Queue
        # determine if its IOS/XE or Nexus and grab all of its neighbors
        ssh = SSHClass(ip=saved[0], username=creds.username, password=creds.password)
        ver_check, cdp_ = ssh.send_command('show version'), ssh.send_command('show cdp neigh det')
    
    ## TODO ##
    # remove unneeded exceptions
    # Added ValueError since its raised by Netmiko when the router-prompt is not found
    except (AuthenticationException, gaierror, SSHException, NetMikoAuthenticationException, NetMikoTimeoutException, ValueError) as e:
        # if we fail to connect - add the device to the "failed" list
        
        ## TODO ###
        # should we remove the failed device from the Queue at this point?
        ## TODO ##
        failed.append(saved[0])
        print "failed to connect to {} due to {}".format(saved[0], e)
        continue

    # determine which parser to use
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
    
    # disconnect from the deivce - append it to visited, and remove it from the Queue
    ssh.disconnect()
    visited.append(saved[0])
    saved.pop(0)
    
    
    for counter, neigh in enumerate(neighbors_data):
        print "processing device {}/{}...".format(counter, len(neighbors_data))
        if (neigh['dev_name'] in saved) or  (neigh['dev_name'] in failed):
            print "{} already saved or failed".format(neigh['dev_name'])
            continue
        
        # skip NetApp
        if neigh['dev_name'].startswith('NA-'):
            continue
        
        try:
            print
            print
            print 'trying to see if {} is reachable...'.format(neigh['dev_name'])
            try_ssh = SSHClass(ip=neigh['dev_name'], username=creds.username, password=creds.password)

        except (AuthenticationException, gaierror, SSHException, NetMikoAuthenticationException, NetMikoTimeoutException, ValueError) as e:
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
            credentials = creds, 
            ssh_port = 22, 
            vendor = 'Cisco', 
            model = neigh['model'],
            device_class = dev_class,
             )

        try:
            device.save()
            print
            print
            print "saved {} to the databse...on to the next!".format(neigh['dev_name'])
            print 
            print 
        except IntegrityError as e:
            print 'Failed to save device {}...due to {}'.format(neigh['dev_name'], e)
            failed.append(neigh['dev_name'])
            continue
        
        saved.append(neigh['dev_name'])
        print
        print
        print "Appending {}, to the 'Saved' list ".format(neigh['dev_name'])
