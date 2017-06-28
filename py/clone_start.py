import socket
import subprocess
from subprocess import PIPE
import shlex
import sqlite3
import sys

_vmdata = '/mnt/vmdata.db'

def _delete_snapshot(vm_id):
	command = '''
	rm -f /home/pi/diff{0}.qcow2
	'''.format(str(vm_id))

	p = _exec_process(command)
	p.wait()

def _exec_process(command):
	args = shlex.split(command)
	p = subprocess.Popen(args, stdout = PIPE)

	return p

def _exec_sql(db, sql):
	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute(sql)
	conn.commit()
	conn.close()

	return

def _exec_sql_by_val(db, sql, val):
	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute(sql, val)
	conn.commit()
	conn.close()

	return

def _get_dbinfo(db, sql):
	conn = sqlite3.connect(db)
	c = conn.cursor()

	data_list = []
	for row in c.execute(sql):
		data_list.append(row)

	conn.close()
	return data_list

def _get_my_ip():
	ip_list = []
	for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]:
		s.connect(('8.8.8.8', 80))
		myip = s.getsockname()[0]
		ip_list.append(myip)
		s.close()
	return ip_list[0]

def _is_start(p):
	while True:
		line = p.stdout.readline()
		sys.stdout.write(line)
		# print('_is_start: {0}'.format(line))
		if line.count('vm start complete') != 0:
			return True

		elif line.count('already in use') != 0:
			return False

		if not line and p.poll() != None:
			pass
			# print('Error')

	return False

def _rename_img_file(from_id, to_id):
	command = '''
	mv /home/pi/diff{0}.qcow2 /home/pi/diff{1}.qcow2
	'''.format(from_id, to_id)

	print(command)

	p = _exec_process(command)
	p.wait()

if __name__ == '__main__':
	args = sys.argv
	from_vm_id = args[1]
	vm_id = args[2]
	vm_ip = args[3]
	vm_port = args[4]
	_rename_img_file(from_vm_id, vm_id)
	ip = _get_my_ip()

	command = '''
	/mnt/sh/start {0} {1} {2}
	'''.format(vm_ip, vm_port, vm_id)
	p = _exec_process(command)

	if not _is_start(p):
		while True:
			sql = 'delete from vmdata where vmip = "{0}"'.format(vm_ip)
			_exec_sql(_vmdata, sql)

			sql = 'insert into vmdata (ipadd, vmip, telnet_port) values (?, ?, ?)'
			val = (-1, -1, vm_port)
			_exec_sql_by_val(_vmdata, sql, val)

			vm_port = str(int(vm_port) + 1)
			sql = 'insert into vmdata (ipadd, vmip, telnet_port) values (?, ?, ?)'
			val = (ip, vm_ip, vm_port)
			_exec_sql_by_val(_vmdata, sql, val)

			# _delete_snapshot(vm_id)
			# vm_id = _create_snapshot(ip, vm_ip)
			sql = 'select id from vmdata where vmip = "{0}"'.format(vm_ip)
			new_vm_id = _get_dbinfo(_vmdata, sql)[0][0]
			_rename_img_file(vm_id, new_vm_id)
			vm_id = new_vm_id

			command = '/mnt/sh/start {0} {1} {2}'.format(vm_ip, vm_port, vm_id)
			p = _exec_process(command)

			if _is_start(p):
				break
