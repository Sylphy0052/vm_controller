#!/usr/bin/python3.5
import subprocess
import os
import shlex
import psutil
import sqlite3
import socket
import threading
import time

user = "pi"
password = "raspberry"

ipdata = "/opt/nfs/ipdata.db"
vmdata = "/opt/nfs/vmdata.db"
clonedata = "/opt/nfs/clonedata.db"

class NotFoundDBError(Exception):
	def __init__(self, value):
		self.value = "{0} is not found.".format(value)
	def __str__(self):
		return repr(self.value)

class NotFoundDBInfoError(Exception):
	def __init__(self, value):
		self.value = "id is not found."
	def __str__(self):
		return repr(self.value)	

class NotDefinedError(Exception):
	def __init__(self, value):
		self.value = "NotDefinedError"
	def __str__(self):
		return repr(self.value)	

def exec_subprocess(command):
	args = shlex.split(command)
	p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	# p = subprocess.Popen(args)


	return p

def create_db():
	if not os.path.isfile(ipdata):
		conn = sqlite3.connect(ipdata)
		c = conn.cursor()

		create_table =  'create table ipdata (id integer primary key, ipadd, type, cpu, mem)'
		c.execute(create_table)
		# print('create ipdata db.')
		
	if not os.path.isfile(vmdata):
		conn = sqlite3.connect(vmdata)
		c = conn.cursor()

		create_table =  'create table vmdata (id integer primary key, ipadd, vmip, telnet_port)'
		c.execute(create_table)
		# print('create vmdata db.')

	if not os.path.isfile(clonedata):
		conn = sqlite3.connect(clonedata)
		c = conn.cursor()

		create_table =  'create table clonedata (id integer primary key, from_ip, to_ip)'
		c.execute(create_table)
		# print('create vmdata db.')

def getMyIP():
	list = []
	for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]:
		s.connect(('8.8.8.8', 80))
		myip = s.getsockname()[0]
		list.append(myip)
		s.close()
	return list[0]

def get_db_info(data):
	if not os.path.isfile(data):
		create_db()
	
	dataname = data.split("/")[3]
	dataname = dataname.split(".")[0]

	conn = sqlite3.connect(data)
	c = conn.cursor()

	sql = 'select * from {0}'.format(dataname)
	datalist = []
	# print(sql)
	for row in c.execute(sql):
		# print(row)
		datalist.append(row)

	conn.close()
	return datalist

def del_db_info(ip):
	if not os.path.isfile(ipdata):
		raise NotFoundDBError(ipdata)
	
	conn = sqlite3.connect(ipdata)
	c = conn.cursor()
	sql = 'delete from ipdata where ipadd = "{0}"'.format(ip)
	c.execute(sql)
	conn.commit()
	conn.close()

	if not os.path.isfile(vmdata):
		raise NotFoundDBError(vmdata)
	
	conn = sqlite3.connect(vmdata)
	c = conn.cursor()

	sql = 'delete from vmdata where ipadd = "{0}"'.format(ip)
	c.execute(sql)
	conn.commit()

	sql = 'delete from vmdata where vmip = "{0}"'.format(ip)
	c.execute(sql)
	conn.commit()
	conn.close()

def clone(vmid, toid):

	iplist = get_dbinfo_by_id(vmdata, vmid)
	ip = iplist[2]
	fromip = iplist[1]
	vmname = ip.split(".")[3]

	iplist = get_dbinfo_by_id(ipdata, toid)
	toip = iplist[1]

	print('clone run... from {0} on {1} to {2}'.format(ip, fromip, toip))
	
	command = "sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} sshpass -p {3} scp -o StrictHostKeyChecking=no /home/pi/diff{4}.qcow2 {5}@{6}:~".format(password, user, fromip, password, vmname, user, toip)
	p = exec_subprocess(command)
	
	try:
		p.wait(timeout=10)
	except subprocess.TimeoutExpired:
		p.kill()
		outs, err = p.communicate()

	command = "sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} python /mnt/py/clone_start.py {3}".format(password, user, toip, vmid)
	
	p = exec_subprocess(command)
	line = p.stdout.readline()
	p.wait()

	print('clone {0} to {1} complete.'.format(fromip, toip))

def migrate(vmid, toid):

	iplist = get_dbinfo_by_id(vmdata, vmid)
	ip = iplist[2]
	fromip = iplist[1]
	telnet_port = iplist[3]
	vmname = ip.split(".")[3]

	iplist = get_dbinfo_by_id(ipdata, toid)
	toip = iplist[1]

	print('migrate run... from {0} on {1} to {2}'.format(ip, fromip, toip))

	command = "sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} sshpass -p {3} scp -o StrictHostKeyChecking=no /home/pi/diff{4}.qcow2 {5}@{6}:~".format(password, user, fromip, password, vmname, user, toip)
	 
	p = exec_subprocess(command)

	try:
	    p.wait(timeout=10)
	except TimeoutExpired:
	    p.kill()
	    print(p.communicate()[1])

	command = "sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} python /mnt/py/migrate_start.py {3} {4}".format(password, user, toip, ip, telnet_port)

	p = exec_subprocess(command)

	try:
		p.wait(timeout=5)
	except subprocess.TimeoutExpired:
		pass

	command = "sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} python /mnt/py/telnet.py {3} {4}".format(password, user, fromip, toip, telnet_port)
	
	p = exec_subprocess(command)

	try:
	    p.wait(timeout=40)
	except TimeoutExpired:
	    p.kill()
	    print(p.communicate()[1])
	
	print("migrate execution fin...")

def get_dbinfo_by_id(dbname, id):
	iplist = get_db_info(dbname)
	
	for ip in iplist:
		if str(ip[0]) == str(id):
			return ip

	raise NotFoundDBInfoError

def vm_start(id):
	ip = get_dbinfo_by_id(ipdata, id)[1]

	print('vmstart on {0}'.format(ip))

	command = 'sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} python /mnt/py/start.py'.format(password, user, ip)

	p = exec_subprocess(command)
	line = p.stdout.readline()

	try:
		p.wait(timeout=50)
	except subprocess.TimeoutExpired:
		print('===error===')
		return

	print('run')

def getIPlist():
	iplist = get_db_info(ipdata)
	result_list = []
	for ip in iplist:
		result_list.append(ip[1])

	result_list = list(set(result_list))
	return result_list

def update(ip):
	# print('---{0} Thread---'.format(ip))
	command = 'sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} python /mnt/py/getHardInfo.py'.format(password, user, ip)
	# print(command)
	p = exec_subprocess(command)

	try:
		p.wait(timeout = 10)
	except subprocess.TimeoutExpired:
		p.kill()
	
	# print('---{0} Thread end---'.format(ip))

def updateInfo(iplist):
	for ip in iplist:
		t = threading.Thread(target=update, args=(ip,))
		t.start()

def getInfo():
	updateData()
	iplist = getIPlist()
	updateInfo(iplist)
	if not os.path.isfile(ipdata):
		raise NotFoundDBError("ipdata.db")
	
	while threading.active_count() > 1:
		pass

	ipdata_list = get_db_info(ipdata)
	vmdata_list = get_db_info(vmdata)
	clonedata_list = get_db_info(clonedata)
	
	print('[ipdata]\n{0:^5}|{1:^15}|{2:^5}|{3:^5}|{4:^5}'.format("id", "ipaddress", "type", "cpu", "mem"))
	for row in ipdata_list:
		print('{0:^5}|{1:^15}|{2:^5}|{3:^5}|{4:^5}'.format(row[0], row[1], row[2], row[3], row[4]))
	line = "=" * 50
	print('\n{0}\n'.format(line))
	print('[vmdata]\n{0:^5}|{1:^15}|{2:^15}|{3:^10}'.format("id", "ipaddress", "vmipaddress", "telnetport"))
	for row in vmdata_list:
		if row[1] == -1:
			continue
		print('{0:^5}|{1:^15}|{2:^15}|{3:^10}'.format(row[0], row[1], row[2], row[3]))
	line = "=" * 50
	print('\n{0}\n'.format(line))
	print('[clonedata]\n{0:^5}|{1:^15}|{2:^15}'.format("id", "from_ipaddress", "clone_ipaddress", "telnetport"))
	for row in clonedata_list:
		if row[1] == -1:
			continue
		print('{0:^5}|{1:^15}|{2:^15}'.format(row[0], row[1], row[2]))

def del_img(vmip):

	vmdata_list = get_db_info(vmdata)

	if len(vmdata_list) == 0:
		return

	for data in vmdata_list:
		if str(data[1]) == str(-1):
			continue

		if str(data[2]) == str(vmip):
			# running_ip = data[1]
			break

	if str(data[1]) == str(-1):
		return

	print('data: {0}'.format(data))
	vmip = data[2].split(".")[3]
	command = 'sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} rm diff{3}.qcow2'.format(password, user, data[1], vmip)
	p = exec_subprocess(command)

def del_ip_info(ip):
	# print("del {0}".format(ip))
	del_img(ip)
	del_db_info(ip)

def connection_confirm(ip):
	# print('connection: {0}'.format(ip))
	command = 'ping -c 1 {0}'.format(ip)
	p = exec_subprocess(command)

	while True:
		line = p.stdout.readline()
		# print(line.decode())
		line = line.decode()
		if line.count('Unreachable'):
			# print('Unreachable {0}'.format(ip))
			del_ip_info(ip)
			break

		if not line and p.poll() != None:
			p.kill()
			# del_ip_info(ip)
			break

def updateData():
	iplist = []
	for ip in get_db_info(ipdata):
		iplist.append(ip[1])

	for ip in get_db_info(vmdata):
		iplist.append(ip[1])
		iplist.append(ip[2])
		
	iplist = list(set(iplist))

	for ip in iplist:
		if str(ip) == str(-1):
			continue
		# print(ip)
		t = threading.Thread(target=connection_confirm, args=(ip,))
		t.start()

	while threading.active_count() != 1:
		pass

def del_all_img(ip):
	command = 'sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} rm *.qcow2'.format(password, user, ip)
	p = exec_subprocess(command)
	line = p.stdout.readline()

def rm_db(command):
	p = exec_subprocess(command)
	p.wait()

def clear_db():

	iplist = []
	for ip in get_db_info(ipdata):
		iplist.append(ip[1])

	iplist = list(set(iplist))

	for ip in iplist:
		t = threading.Thread(target=del_all_img, args=(ip,))
		t.start()



	command1 = 'rm /opt/nfs/ipdata.db'
	command2 = 'rm /opt/nfs/vmdata.db'
	command3 = 'rm /opt/nfs/clonedata.db'

	t1 = threading.Thread(target=rm_db, args=(command1,))
	t2 = threading.Thread(target=rm_db, args=(command2,))
	t3 = threading.Thread(target=rm_db, args=(command3,))
	
	t1.start()
	t2.start()
	t3.start()

	create_db()

	while threading.active_count() != 1:
		pass

def mount_ip(ip):
	myip = getMyIP()
	mount_in_ip(myip, ip)

def add_ip(ip):
	if not os.path.isfile(ipdata):
		raise NotFoundDBError(ipdata)

	mount_ip(ip)
	update(ip)

def halt(id):
	iplist = get_dbinfo_by_id(vmdata, id)
	ip = iplist[2]

	command = 'sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} sudo halt'.format('linux', 'root', ip)
	p = exec_subprocess(command)

	try:
		p.wait(timeout=10)
	except subprocess.TimeoutExpired:
		pass

	del_ip_info(ip)

def help():
	print('migrate vmid ipid')
	print('clone vmid ipid')
	print('start ipid')
	print('info')
	print('del_db')
	print('quit or exit')

def quit():
	print('Bye')

def reboot(ip):
	command = 'sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} sudo reboot'.format(password, user, ip)
	p = exec_subprocess(command)

	try:
		p.wait(timeout=10)
	except subprocess.TimeoutExpired:
		pass

def all_reboot():
	t1 = threading.Thread(target=reboot, args=('192.168.3.2',))
	t2 = threading.Thread(target=reboot, args=('192.168.3.11',))

	t1.start()
	t2.start()

	while threading.active_count() != 1:
		pass

def mount_in_ip(myip, ip):
	command = 'sshpass -p {0} ssh -o StrictHostKeyChecking=no {1}@{2} /home/pi/sh/mount {3}'.format(password, user, ip, myip)
	p = exec_subprocess(command)
	p.wait(timeout=5)

def mount():

	myip = getMyIP()

	iplist = []
	for ip in get_db_info(ipdata):
		iplist.append(ip[1])

	iplist = list(set(iplist))

	for ip in iplist:
		t = threading.Thread(target=mount_in_ip, args=(myip, ip,))
		t.start()

	while threading.active_count() != 1:
		pass

def start():
	create_db()
	updateData()
	mount()

if __name__ == '__main__':
	start()

	while 1:

		# print("What do you want to do?")

		command = input('\n>> ')

		if command == '':
			quit()
			break

		commands = command.split()


		if commands[0] == 'clone':
			if len(commands) == 3:
				clone(commands[1], commands[2])
			else:
				print('error... Put \"clone ip1 ip2\"')

		elif commands[0] == 'migrate':
			if len(commands) == 3:
				migrate(commands[1], commands[2])
			else:
				print('error... Put \"migrate ip1 ip2\"')

		elif commands[0] == 'info':
			if len(commands) == 1:
				getInfo()
			else:
				print('error... Put \"info\"')

		elif commands[0] == 'start':
			if len(commands) == 2:
				vm_start(commands[1])
			else:
				print('error... Put \"start ip\"')

		# elif commands[0] == 'update':
		# 	if len(commands) == 1:
		# 		updateData()
		# 	else:
		# 		print('error... Put \"update\"')

		elif commands[0] == 'del_db':
			if len(commands) == 1:
				all_reboot()
				clear_db()
				# add_ip("192.168.3.2")
				# add_ip("192.168.3.11")
			else:
				print('error... Put\"del_db\"')

		elif commands[0] == 'reboot':
			if len(commands) == 1:
				all_reboot()
			else:
				print('error... Put\"reboot\"')	

		elif commands[0] == 'halt':	
			if len(commands) == 2:
				halt(commands[1])	
			else:
				print('error... Put\"halt id\"')

		elif commands[0] == 'add':
			if len(commands) == 1:
				add_ip("192.168.3.2")
				add_ip("192.168.3.11")
			elif len(commands) == 2:
				add_ip(commands[1])
			else:
				print('error... Put\"add ip\"')

		# elif commands[0] == 'help':
		# 	if len(commands) == 1:
		# 		help()
		# 	else:
		# 		print('error... Put \"help\"')

		elif commands[0] == 'quit' or commands[0] == 'exit':
			quit()
			break

		else:
			help()
