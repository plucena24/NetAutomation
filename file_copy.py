import netmiko
import multiprocessing

device_type = 'cisco_xe'
SSHClass = netmiko.ssh_dispatcher(device_type=device_type)
username = 'admin'
password = 'password'


def copy_img(remote_dev, ftp_server, file_name, ftpuser='cisco', ftppass='cisco', vrf='', delay_factor=2, max_loops=400):

    if device_type == 'cisco_xe':
        url = 'ftp://{ftpuser}:{ftppass}@{ftp_server}/{file_name} flash:{file_name}'.format(ftpuser=ftpuser, ftppass=ftppass, ftp_server=ftp_server, file_name=file_name)
        print url

    if device_type == 'cisco_nxos':
        url = 'ftp://{ftpuser}:{ftppass}@{ftp_server}/{file_name} bootflash:{file_name} vrf {vrf}'.format(ftpuser=ftpuser, ftppass=ftppass, ftp_server=ftp_server, file_name=file_name)
        print url

    net_con = SSHClass(remote_dev, username=username, password=password)

    output = net_con.send_command('copy {url}'.format(url=url))

    if device_type == 'cisco_xe':
        output += net_con.send_command('\n', delay_factor=delay_factor, max_loops=max_loops)
        return output

    if device_type == 'cisco_nxos':
        output += net_con.send_command('{ftppass}'.format(ftppass=ftppass), max_loops=max_loops)

if __name__ == '__main__':


    file_name = 'c1841-adventerprisek9-mz.151-4.M9.bin'
    ftp_server = '192.168.1.60'
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())


    devices_to_copy = ['192.168.1.254']

    pool_results = [pool.apply_async(copy_img, args=(dev, ftp_server, file_name)) for dev in devices_to_copy]

    pool.close()
    pool.join()

    for result in pool_results:
        print result.get()

