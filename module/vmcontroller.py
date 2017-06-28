import ipaddress
import netifaces
import os
import sqlite3
import shlex
import subprocess
from subprocess import TimeoutExpired, PIPE
from time import time
import threading

_my_ip1 = ''
_my_ip2 = ''
_my_mask = ''
#_my_ip = '192.10.1.15'
#_my_mask = '255.255.255.0'
_net_ip = ''

_usr = 'pi'
_pass = 'raspberry'

_vm_usr = 'root'
_vm_pass = 'linux'

_ipdata = '/opt/nfs/ipdata.db'
_vmdata = '/opt/nfs/vmdata.db'
_clonedata = '/opt/nfs/clonedata.db'

_config_flg = False

_start_time = 0.0

class Config():
	def __init__(self):
		self.mig_cpu = 100
		self.mig_mem = 100
		self.clone_cpu = 100
		self.clone_mem = 100

	def clone_set_cpu(self, cpu):
		self.clone_cpu = cpu

	def clone_set_mem(self, mem):
		self.clone_mem = mem

class IpData():
	def __init__(self):
		self.id = ''
		self.ip = ''
		self.type = ''
		self.cpu = ''
		self.mem = ''

	def set_data(self, id, ip, type, cpu, mem):
		self.id = id
		self.ip = ip
		self.type = type
		self.cpu = cpu
		self.mem = mem

	def print(self):
		print(self.id, self.ip, self.type, self.cpu, self.mem)
		print('[ipdata]\n{0:^5}|{1:^15}|{2:^5}|{3:^5}|{4:^5}'.format("id", "ipaddress", "type", "cpu", "mem"))
		print('{0:^5}|{1:^15}|{2:^5}|{3:^5.1f}|{4:^5.1f}'.format(self.id, self.ip, self.type, self.cpu, self.mem))
		print()

class VmData():
	def __init__(self):
		self.id = ''
		self.ip = ''
		self.vmip = ''
		self.port = ''

	def set_data(self, id, ip, vmip, port):
		self.id = id
		self.ip = ip
		self.vmip = vmip
		self.port = port

	def print(self):
		sql = 'select id, ipadd, vmip, telnet_port from vmdata where ipadd <> -1'
		print('[vmdata]\n{0:^5}|{1:^15}|{2:^15}|{3:^10}'.format("id", "ipaddress", "vmipaddress", "telnetport"))
		print('{0:^5}|{1:^15}|{2:^15}|{3:^10}'.format(self.id, self.ip, self.vmip, self.port))
		print()

def _add_ssh(ip):
	command = '''
	ssh-keygen -f
	"/home/pi/.ssh/known_hosts"
	-R {0}'''.format(ip)
	p = _exec_process(command)
	try:
		p.wait(timeout = 10)
	except TimeoutExpired:
		print('ssh error')

def _all_mount():
	sql = 'select ipadd from ipdata where ipadd <> "-1" and type = 1'
	ip_list = []
	for ip in _get_dbinfo(_ipdata, sql):
		ip_list.append(ip[0])

	print(ip_list)
	for ip in ip_list:
		command = '''
		sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2}
		/home/pi/sh/mount {3}
		'''.format(_pass, _usr, ip, _my_ip)

		p = _exec_process(command)
		p.wait()

def _check_config():
	if _config_flg == False:
		_config()

def _config():
	global _config_flg
	_get_my_ip()
	_config_net_ip()
	_all_mount()
	_config_flg = True

def _config_net_ip():
	global _net_ip
	# print(_my_ip + " : " + _my_mask)
	net_ip = ipaddress.ip_address(int(_my_ip) & int(_my_mask))
	net_split = str(net_ip).split('.')
	for i in range(4):
		if net_split[i] == str(0):
			break
		_net_ip += net_split[i]
		if i == 3:
			break
		_net_ip += '.'

	print('net_ip: {0}'.format(_net_ip))

def _confirm_connection(ip):
	command = 'ping -c 1 {0}'.format(ip)
	p = _exec_process(command)

	while True:
		line = p.stdout.readline().decode()
		if line.count('Unreachable') or line.count('100%'):
			print('delete {0}'.format(ip))
			_delete_ip_info(ip)
			break

		if not line and p.poll() != None:
			# _update_info(ip)
			break

def _create_db():
	print('db create')

	if not os.path.isfile(_ipdata):
		conn = sqlite3.connect(_ipdata)
		c = conn.cursor()

		create_table = '''
		create table ipdata (
		id integer primary key,
		ipadd text,
		type integer,
		cpu real,
		mem real
		)'''

		c.execute(create_table)

	if not os.path.isfile(_vmdata):
		conn = sqlite3.connect(_vmdata)
		c = conn.cursor()

		create_table = '''
		create table vmdata (
		id integer primary key,
		ipadd text,
		vmip text,
		telnet_port integer
		)'''

		c.execute(create_table)

	if not os.path.isfile(_clonedata):
		conn = sqlite3.connect(_clonedata)
		c = conn.cursor()

		create_table =  '''
		create table clonedata (
		id integer primary key,
		from_ip text,
		to_ip text
		)'''

		c.execute(create_table)

def _define_vm_net(pm_ip):
	pm_ip = ipaddress.ip_address(pm_ip)
	net_ip = ipaddress.ip_address(int(pm_ip) & int(_my_mask))
	net_split = str(net_ip).split('.')
	ret = ''
	for i in range(4):
		if net_split[i] == str(0):
			break
		ret += net_split[i]
		if i == 3:
			break
		ret += '.'

	print('net_ip: {0}'.format(ret))
	return ret

def _define_vm_ip(pm_ip):
	sql = 'select ipadd from ipdata where ipadd <> "-1" order by ipadd desc'
	ip_list = []
	for ip in _get_dbinfo(_ipdata, sql):
		ip_list.append(ip[0])

	least_ip = int(ip_list[0].split('.')[3]) + 1
	print('ip:', least_ip)

	net_ip = _define_vm_net(pm_ip)

	print(ip_list)
	for i in range(least_ip, 255):
		ip = net_ip + str(i)
		if ip_list.count(ip) == 0:
			print('checking: {0}'.format(ip))
			command = 'ping -c 1 {0}'.format(ip)
			p = _exec_process(command)

			while True:
				line = p.stdout.readline().decode()
				if line.count('Unreachable') or line.count('100%'):
					return ip

				if not line and p.poll() != None:
					break

def _define_vm_port():
	sql = 'select telnet_port from vmdata'
	vm_port_list = []
	for port in _get_dbinfo(_vmdata, sql):
		vm_port_list.append(port[0])

	print(vm_port_list)
	for i in range(1024, 49151):
		port = str(i)
		print()
		if port == str(4449):
			continue
		if vm_port_list.count(port) == 0:
			return port

def _delete_ip_info(ip):
	sql = 'select type from ipdata where ipadd = "{0}"'.format(ip)
	type = _get_dbinfo(_ipdata, sql)[0][0]
	print('_delete_ip_info {0}:{1}'.format(ip, type))
	if type == 1:
		_delete_ip_data(ip)

	elif type == 2:
		_delete_ip_data(ip)
		_delete_vm_data(ip)

	print('_delete_ip_info end')

def _delete_ip_data(ip):
	sql = 'delete from ipdata where ipadd = "{0}"'.format(ip)
	_exec_sql(_ipdata, sql)

def _delete_vm_data(ip):
	sql = 'select id, ipadd from vmdata where vmip = "{0}"'.format(ip)
	ip_data = _get_dbinfo(_vmdata, sql)[0]

	vm_id = ip_data[0]
	running_ip = ip_data[1]

	command = '''
	sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2}
	rm diff{3}.qcow2
	'''.format(_pass, _usr, running_ip, vm_id)
	print(command)
	p = _exec_process(command)
	try:
		p.wait(timeout = 10)
	except TimeoutExpired:
		pass

	sql = 'update vmdata set ipadd = ?, vmip = ? where vmip = ?'
	val = (-1, -1, ip)
	_exec_sql_by_val(_vmdata, sql, val)

	sql = 'delete from clonedata where from_ip = "{0}"'.format(ip)
	_exec_sql(_clonedata, sql)

	sql = 'delete from clonedata where to_ip = "{0}"'.format(ip)
	_exec_sql(_clonedata, sql)

def _exec_process(command):
	args = shlex.split(command)
	p = subprocess.Popen(args, stdout = PIPE)

	return p

def _exec_sql(db, sql):
	if not os.path.isfile(db):
		_create_db()

	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute(sql)
	conn.commit()
	conn.close()

	return

def _exec_sql_by_val(db, sql, val):
	# print('db: {0} sql: {1} val: {2}'.format(db, sql, val))
	if not os.path.isfile(db):
		_create_db()

	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute(sql, val)
	conn.commit()
	conn.close()

	return

def _get_dbinfo(db, sql):
	if not os.path.isfile(db):
		_create_db()

	conn = sqlite3.connect(db)
	c = conn.cursor()

	data_list = []
	for row in c.execute(sql):
		data_list.append(row)

	conn.close()
	return data_list

def _get_dbinfo_by_id(db, id):
	db_name = db.split('/')[3]
	db_name = db_name.split('.')[0]
	sql = 'select * from {0} where id = {1}'.format(db_name, id)
	ip_list = _get_dbinfo(db, sql)

	return ip_list[0]

def _get_my_ip():
	global _my_ip, _my_mask
	net_name = ''
	for name in netifaces.interfaces():
		if name.count('lo') != 0:
			continue
		elif netifaces.ifaddresses(name).get(netifaces.AF_INET) == None:
			continue
		else:
			net_name = name
			break

	info = netifaces.ifaddresses(net_name).get(netifaces.AF_INET)
	print(info)
	_my_ip = ipaddress.ip_address(info[0]['addr'])
	_my_mask = ipaddress.ip_address(info[0]['netmask'])

	# print("my_ip : " + _my_ip + " / my_mask : " + _my_mask)
	return ipaddress.ip_address(info[0]['addr']), ipaddress.ip_address(info[0]['netmask'])

def _print_info():
	sql = 'select id, ipadd, type, cpu, mem from ipdata'
	ip_data_list = _get_dbinfo(_ipdata, sql)
	print('''
		[ipdata]\n{0:^5}|{1:^15}|{2:^5}|{3:^5}|{4:^5}
		'''.format("id", "ipaddress", "type", "cpu", "mem"))
	for row in ip_data_list:
		# print(row)
		print('{0:^5}|{1:^15}|{2:^5}|{3:^5.1f}|{4:^5.1f}'.format(row[0], row[1], row[2], row[3], row[4]))
	line = "=" * 50
	print('\n{0}'.format(line))

	sql = 'select id, ipadd, vmip, telnet_port from vmdata where ipadd <> -1'
	vm_data_list = _get_dbinfo(_vmdata, sql)
	print('''
		[vmdata]\n{0:^5}|{1:^15}|{2:^15}|{3:^10}
		'''.format("id", "ipaddress", "vmipaddress", "telnetport"))
	for row in vm_data_list:
		print('{0:^5}|{1:^15}|{2:^15}|{3:^10}'.format(row[0], row[1], row[2], row[3]))
	line = "=" * 50
	print('\n{0}'.format(line))

	sql = 'select * from clonedata'
	clone_data_list = _get_dbinfo(_clonedata, sql)
	print('[clonedata]\n{0:^5}|{1:^15}|{2:^15}'.format("id", "from_ipaddress", "clone_ipaddress", "telnetport"))
	for row in clone_data_list:
		print('{0:^5}|{1:^15}|{2:^15}'.format(row[0], row[1], row[2]))

def _time_start():
	global _start_time
	_start_time = time()

def _time_end():
	elapsed_time = time() - _start_time
	print('time: {0:.2f}[sec]'.format(elapsed_time))

def _update_data():
	sql = 'select ipadd from ipdata'
	ip_list = _get_dbinfo(_ipdata, sql)
	for data in ip_list:
		ip = data[0]
		print('ip: {0}'.format(ip))
		t = threading.Thread(target = _confirm_connection, args = (ip,))
		t.start()

	while threading.active_count() > 1:
		pass

def _update_info(ip):
	sql = 'select type from ipdata where ipadd = "{0}"'.format(ip)
	type = _get_dbinfo(_ipdata, sql)

	if type == [] or type[0][0] == 1:
		command = '''
		sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2}
		python /mnt/py/getHardInfo.py
		'''.format(_pass, _usr, ip)

		p = _exec_process(command)
		p.wait()


	elif type[0][0] == 2:
		_update_vm_info(ip)

def _update_vm_info(vm_ip):
	command = '''
	sshpass -p {0} ssh -t -o StrictHostKeyChecking=no
	{1}@{2}
	top -d 60
	'''.format(_vm_pass, _vm_usr, vm_ip)

	args = shlex.split(command)

	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	i = 0
	while True:
		line = p.stdout.readline().decode()
		if i ==2:
			split = shlex.split(line)
			cpu = float(100) - float(split[7])
		elif i == 3:
			split = shlex.split(line)
			mem = float(split[7]) / float(split[3]) * 100
		i += 1
		if i == 4:
			break

	p.terminate()
	sql = 'update ipdata set cpu = ?, mem = ? where ipadd = ?'
	val = (cpu, mem, vm_ip)
	_exec_sql_by_val(_ipdata, sql, val)

def add(ip):
	_time_start()
	_check_config()
	if not os.path.isfile(_ipdata):
		_create_db()

	command = '''
	sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2}
	/home/pi/sh/mount {3}
	'''.format(_pass, _usr, ip, _my_ip)

	print(command)

	p = _exec_process(command)
	p.wait()

	_add_ssh(ip)
	_update_info(ip)
	_time_end()

def clone(vm_id, to_id):
	_time_start()
	_check_config()
	vm_data = _get_dbinfo_by_id(_vmdata, vm_id)
	to_data = _get_dbinfo_by_id(_ipdata, to_id)

	from_ip = vm_data[1]
	to_ip = to_data[1]
	vm_type = to_data[2]
	vm_ip = vm_data[2]

	if vm_type != 1:
		print('Not VM_Machine')
		return

	print('clone run... from {0} on {1} to {2}'.format(vm_ip, from_ip, to_ip))

	to_vm_ip = _define_vm_ip(to_ip)
	to_vm_port = _define_vm_port()

	command = """
	sshpass -p {0}
	ssh -o StrictHostKeyChecking=no {1}@{2}
	sshpass -p {3}
	scp -o StrictHostKeyChecking=no
	/home/pi/diff{4}.qcow2 {5}@{6}:~
	""".format(_pass, _usr, from_ip, _pass, vm_id, _usr, to_ip)

	p = _exec_process(command)
	p.wait()

	sql = 'insert into vmdata (ipadd, vmip, telnet_port) values (?, ?, ?)'
	val = (to_ip, to_vm_ip, to_vm_port)
	_exec_sql_by_val(_vmdata, sql, val)

	sql = 'select id from vmdata where vmip = "{0}"'.format(to_vm_ip)
	to_vm_id = _get_dbinfo(_vmdata, sql)[0][0]

	sql = 'insert into clonedata (from_ip, to_ip) values (?, ?)'
	val = (vm_ip, to_vm_ip)
	_exec_sql_by_val(_clonedata, sql, val)

	sql = 'insert into ipdata (ipadd, type) values (?, ?)'
	val = (to_vm_ip, 2)
	_exec_sql_by_val(_ipdata, sql, val)

	command = """
	sshpass -p {0}
	ssh -o StrictHostKeyChecking=no
	{1}@{2} python /mnt/py/clone_start.py {3} {4} {5} {6}
	""".format(_pass, _usr, to_ip, vm_id, to_vm_id, to_vm_ip, to_vm_port)

	print(command)

	p = _exec_process(command)
	try:
		p.wait(timeout = 100)
	except TimeoutExpired:
		pass

	_add_ssh(to_vm_ip)
	_update_vm_info(vm_ip)
	print('clone complete.')
	_time_end()

def get_cpu_larger_than_val(val):
	_check_config()
	_update_data()

	sql = 'select * from ipdata where cpu >= {0} and type = 1 order by cpu desc'.format(val)
	data_list = _get_dbinfo(_ipdata, sql)
	ip_list = []

	if len(data_list) == 0:
		pass

	else:
		for data in data_list:
			ip_c = IpData()
			ip_c.set_data(data[0], data[1], data[2], data[3], data[4])
			ip_list.append(ip_c)

	return ip_list

def get_cpu_least():
	_check_config()
	_update_data()

	sql = 'select * from ipdata where type = 1 order by cpu asc limit 1'
	data_list = _get_dbinfo(_ipdata, sql)

	if len(data_list) == 0:
		return None

	else:
		for data in data_list:
			ip_c = IpData()
			ip_c.set_data(data[0], data[1], data[2], data[3], data[4])
			return ip_c

def get_info():
	_check_config()
	_update_data()

	sql = 'select * from ipdata'
	data_list = _get_dbinfo(_ipdata, sql)
	ip_list = []
	for data in data_list:
		ip_c = IpData()
		ip_c.set_data(data[0], data[1], data[2], data[3], data[4])
		ip_list.append(ip_c)

	return ip_list

def get_vm_info():
	_check_config()
	_update_data()

	sql = 'select * from vmdata'
	data_list = _get_dbinfo(_vmdata, sql)
	vm_list = []
	for data in data_list:
		vm_c = VmData()
		vm_c.set_data(data[0], data[1], data[2], data[3])
		vm_list.append(vm_c)

	return vm_list

def get_vm_info_by_id(id):
	_check_config()
	ip = _get_dbinfo_by_id(_ipdata, id)[1]
	sql = 'select id from vmdata where ipadd = {0}'.format(ip)
	data_list = _exec_sql(_vmdata, sql)
	return data_list[0][0]

def get_mem_larger_than_val(val):
	_check_config()
	_update_data()

	sql = 'select * from ipdata where mem >= {0} and type = 1 order by mem desc'.format(val)
	data_list = _get_dbinfo(_ipdata, sql)
	ip_list = []

	if len(data_list) == 0:
		pass

	else:
		for data in data_list:
			ip_c = IpData()
			ip_c.set_data(data[0], data[1], data[2], data[3], data[4])
			ip_list.append(ip_c)

	return ip_list

def get_mem_least():
	_check_config()
	_update_data()

	sql = 'select * from ipdata where type = 1 order by mem asc limit 1'
	data_list = _get_dbinfo(_ipdata, sql)

	if len(data_list) == 0:
		return None

	else:
		for data in data_list:
			ip_c = IpData()
			ip_c.set_data(data[0], data[1], data[2], data[3], data[4])
			return ip_c

def info():
	_time_start()
	_check_config()
	_update_data()

	_print_info()
	_time_end()
	print('\n\n')

def migrate(vm_id, to_id):
	_time_start()
	_check_config()
	vm_data = _get_dbinfo_by_id(_vmdata, vm_id)
	to_data = _get_dbinfo_by_id(_ipdata, to_id)

	from_ip = vm_data[1]
	to_ip = to_data[1]
	vm_ip = vm_data[2]

	if to_data[2] != 1:
		print('Not VM_Machine')
		return

	print('migrate run... from {0} on {1} to {2}'.format(vm_ip, from_ip, to_ip))

	vm_port = vm_data[3]
	to_vm_port = _define_vm_port()
	to_vm_ip = _define_vm_ip(to_ip)

	command = '''
	sshpass -p {0}
	ssh -o StrictHostKeyChecking=no {1}@{2}
	sshpass -p {3}
	scp -o StrictHostKeyChecking=no
	/home/pi/diff{4}.qcow2 {5}@{6}:/home/pi/
	'''.format(_pass, _usr, from_ip, _pass, vm_id, _usr, to_ip)

	print(command)
	p = _exec_process(command)
	p.wait()

	print('migration')
	print('to vm_ip : {0}'.format(to_vm_ip))
	command = '''
	sshpass -p {0}
	ssh -o StrictHostKeyChecking=no
	{1}@{2} python /mnt/py/migrate_start.py {3} {4} {5}
	'''.format(_pass, _usr, from_ip, vm_id, to_vm_port, to_vm_ip)
	p = _exec_process(command)
	try:
		p.wait(timeout = 30)
	except TimeoutExpired:
		pass

	print('telnet')
	command = '''
	sshpass -p {0}
	ssh -o StrictHostKeyChecking=no
	{1}@{2} python /mnt/py/telnet.py {3} {4}
	'''.format(_pass, _usr, from_ip, to_ip, vm_port)
	p = _exec_process(command)
	try:
		p.wait(timeout = 90)
	except TimeoutExpired:
		print('migrate error')

	sql = '''
	update vmdata set ipadd = ?, vmip = ?
	where vmip = ?
	'''
	val = (str(-1), str(-1), vm_ip)
	_exec_sql_by_val(_vmdata, sql, val)

	sql = '''
	insert into vmdata (ipadd, vmip, telnet_port) values (?, ?, ?)
	'''
	val = (to_ip, to_vm_ip, to_vm_port)
	_exec_sql_by_val(_vmdata, sql, val)

	command = '''
	sshpass -p {0}
	ssh -o StrictHostKeyChecking=no {1}@{2}
	rm /home/pi/diff{3}.qcow2
	'''.format(_pass, _usr, from_ip, vm_id)
	p = _exec_process(command)
	try:
		p.wait(timeout = 20)
	except TimeoutExpired:
		print('migrate error')

	_update_vm_info(vm_ip)
	print('migrate complete.')
	_time_end()

def start_vm(id):
	_time_start()
	_check_config()
	vm_type = _get_dbinfo_by_id(_ipdata, id)[2]
	if vm_type != 1:
		print('Not VM_Machine.')
		return
	ip = _get_dbinfo_by_id(_ipdata, id)[1]
	vm_ip = _define_vm_ip(ip)
	vm_port = _define_vm_port()

	print('vm start {0} on {1} port:{2}'.format(ip, vm_ip, vm_port))

	sql = 'insert into vmdata (ipadd, vmip, telnet_port) values (?, ?, ?)'
	val = (ip, vm_ip, vm_port)
	_exec_sql_by_val(_vmdata, sql, val)

	sql = 'insert into ipdata (ipadd, type) values (?, ?)'
	val = (vm_ip, 2)
	_exec_sql_by_val(_ipdata, sql, val)

	command = '''
	sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2}
	python /mnt/py/start.py {3} {4} {5}
	'''.format(_pass, _usr, ip, ip, vm_ip, vm_port)
	print(command)
	p = _exec_process(command)
	try:
		p.wait(timeout = 100)
	except TimeoutExpired:
		print('start error')

	_add_ssh(vm_ip)
	_update_vm_info(vm_ip)
	print('vm start complete.')
	_time_end()
