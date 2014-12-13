import netmiko
import multiprocessing

device_type = 'cisco_xe'
SSHClass = netmiko.class_dispatcher(device_type=device_type)



def copy_img(remote_dev, file_name, ftpuser='cisco', ftppass='cisco', vrf='', max_loops=200):

    if device_type == 'cisco_xe':
        url = 'ftp://{ftpuser}:{ftppass}@{remote_dev}/{file_name}'.format(ftpuser=ftpuser, ftppass=ftppass, remote_dev=remote_dev, file_name=file_name)

    if device_type == 'cisco_nxos':
        url = 'ftp://{ftpuser}:{ftppass}@{remote_dev}/{file_name} vrf {vrf}'.format(ftpuser=ftpuser, ftppass=ftppass, remote_dev=remote_dev, file_name=file_name)

    net_con = SSHClass(remote_dev, username=username, password=password)

    output = net_con.send_command('copy {url}'.format(url=url))

    if device_type == 'cisco_nxos':

        output += net_con.send_command('{ftppass}'.format(ftppass=ftppass))


pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())

devices_to_copy = []

pool_results = [pool.apply_asynclo]
