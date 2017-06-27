import array
import fcntl
import os
import psutil
import socket
import sqlite3
import struct
import sys
import threading

_ipdata = '/mnt/ipdata.db'
_vmdata = '/mnt/vmdata.db'
_clonedata = '/mnt/clonedata.db'

def _create_db():
	# print('db create')

	if not os.path.isfile(_ipdata):
		conn = sqlite3.connect(_ipdata)
		c = conn.cursor()

		create_table = 'create table ipdata (id integer primary key, ipadd, type, cpu, mem)'
		c.execute(create_table)

	if not os.path.isfile(_vmdata):
		conn = sqlite3.connect(_vmdata)
		c = conn.cursor()

		create_table = 'create table vmdata (id integer primary key, ipadd, vmip, telnet_port)'
		c.execute(create_table)

	if not os.path.isfile(_clonedata):
		conn = sqlite3.connect(_clonedata)
		c = conn.cursor()

		create_table =  'create table clonedata (id integer primary key, from_ip, to_ip)'
		c.execute(create_table)

def _exec_sql(db, sql, val):
	if not os.path.isfile(db):
		_create_db()

	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute(sql, val)
	conn.commit()
	conn.close()

	return

def _get_my_ip():
	is_64bits = sys.maxsize > 2**32
	struct_size = 40 if is_64bits else 32
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	max_possible = 8
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

		result_dict['ip'] = socket.inet_ntoa(namestr[i+20:i+24])
		_netmask = fcntl.ioctl(s.fileno(), 0x891b, struct.pack('256s', iface_name[:15]))
		result_dict['netmask'] = socket.inet_ntoa(_netmask[20:24])
		result_list.append(result_dict)

	return result_list[0]['ip']

def _is_my_ip(my_ip):
	if not os.path.isfile(_ipdata):
		_create_db()

	conn = sqlite3.connect(_ipdata)
	c = conn.cursor()

	sql = 'select * from ipdata where ipadd = "{0}"'.format(my_ip)

	for row in c.execute(sql):
		conn.close()
		return True

	conn.close()
	return False

def main():
	type = 1
	cpu = psutil.cpu_percent()
	mem = psutil.virtual_memory().percent

	# print('cpu: {0} mem: {1}'.format(cpu, mem))

	my_ip = _get_my_ip()

	if _is_my_ip(my_ip):
		sql = 'update ipdata set cpu = ?, mem = ? where ipadd = ?'
		val = (cpu, mem, my_ip)
		_exec_sql(_ipdata, sql, val)

	else:
		sql = 'insert into ipdata (ipadd, type, cpu, mem) values (?, ?, ?, ?)'
		val = (my_ip, type, cpu, mem)
		_exec_sql(_ipdata, sql, val)
	t=threading.Timer(1, main)
	t.start()

if __name__ == '__main__':
	t = threading.Thread(target=main)
	t.start()
