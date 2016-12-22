import sys
import socket
import fcntl
import struct
import array
import ipaddress

def get_my_ip():
    is_64bits = sys.maxsize > 2**32
    struct_size = 40 if is_64bits else 32
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    max_possible = 8 # initial value
    while True:
        bytes = max_possible * struct_size
        names = array.array('B', b'\0' * bytes)
        outbytes = struct.unpack('iL', fcntl.ioctl(
            s.fileno(),
            0x8912, 
            struct.pack('iL', bytes, names.buffer_info()[0])
        ))[0]
        if outbytes == bytes:
            max_possible *= 2
        else:
            break
    namestr = names.tostring()
    result_list = []
    for i in range(0, outbytes, struct_size):
        result_dict = {}
        iface_name = namestr[i:i+16].split(b'\0', 1)[0]
        if iface_name.decode().count('lo') != 0:
        	continue

        # iface_addr = socket.inet_ntoa(namestr[i+20:i+24])
        result_dict['ip'] = socket.inet_ntoa(namestr[i+20:i+24])
        _netmask = fcntl.ioctl(s.fileno(), 0x891b, struct.pack('256s', iface_name[:15]))
        # iface_netmask = socket.inet_ntoa(_netmask[20:24])
        result_dict['netmask'] = socket.inet_ntoa(_netmask[20:24])
        result_list.append(result_dict)
        return result_dict
        # .append((iface_name.decode(), iface_addr, iface_mac, iface_netmask, iface_brdaddr))
    
    return result_list

def check_host(dict):
	ip = dict['ip']
	nm = dict['netmask']

	print('ip: {0} netmask: {1}'.format(ip, nm))
	ip_split = str(ip).split('.')
	ip = int(ip_split[0]) << 24 | int(ip_split[1]) << 16 | int(ip_split[2]) << 8 | int(ip_split[3])
	
	nm_split = str(nm).split('.')
	nm = int(nm_split[0]) << 24 | int(nm_split[1]) << 16 | int(nm_split[2]) << 8 | int(nm_split[3])
	
	host = ipaddress.IPv4Address(ip & nm)

	print(host)

	host_split = str(host).split('.')
	host = '.'.join([host_split[0], host_split[1], host_split[2], '101'])
	host = ipaddress.IPv4Address(host)
	print(host)


	if info.netmask <= ipaddress.ip_address('255.0.0.0'):
		print('class A')
	elif info.netmask <= ipaddress.ip_address('255.255.0.0'):
		print('class B')
	elif info.netmask <= ipaddress.ip_address('255.255.255.0'):
		print('class C')
	else:
		print('error')

if __name__ == '__main__':
	dict = get_my_ip()
	ip = dict['ip'] + '/' + dict['netmask']
	info = ipaddress.ip_network(ip, strict=False)
	check_host(dict)
	print(info)
	print(info.netmask)
	# print(list)