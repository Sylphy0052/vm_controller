import os
import shlex
import sqlite3
import subprocess
import sys

_vm_usr = 'root'
_vm_pass = 'linux'

_ipdata = '/mnt/ipdata.db'
_vmdata = '/mnt/vmdata.db'

def _create_snapshot(ip, vm_ip):
	print('_create_snapshot {0} {1}'.format(ip, vm_ip))

	sql = 'select id from vmdata where vmip = "{0}"'.format(vm_ip)
	vm_id = _get_dbinfo(_vmdata, sql)[0][0]

	command = '''
	qemu-img create -b /mnt/image.qcow2
	-f qcow2 /home/pi/diff{0}.qcow2
	'''.format(str(vm_id))

	p = _exec_process(command)
	p.wait()

	print('id: {0}'.format(vm_id))
	return vm_id

def _delete_snapshot(vm_id):
	command = '''
	rm -f /home/pi/diff{0}.qcow2
	'''.format(str(vm_id))

	p = _exec_process(command)
	p.wait()

def _exec_process(command):
	args = shlex.split(command)
	p = subprocess.Popen(args, stdout = subprocess.PIPE)

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

def _is_my_info(ip):
	sql = 'select * from ipdata where ipadd = "{0}"'.format(ip)
 	ip_list = _get_dbinfo(_ipdata, sql)
 	if len(ip_list) == 0:
 		return False
 	else:
 		return True

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

# def _update_vm_info(vm_ip):
	# command = '''
	# sshpass -p {0} ssh -o StrictHostKeyChecking=no
	# {1}@{2}
	# top -d 60
	# '''.format(_vm_pass, _vm_usr, vm_ip)
    #
	# args = shlex.split(command)
    #
	# p = subprocess.Popen(args, stdout=subprocess.PIPE)
	# i = 0
	# while True:
	# 	line = p.stdout.readline().decode()
	# 	if i ==2:
	# 		split = shlex.split(line)
	# 		print(split)
	# 		cpu = float(100) - float(split[7])
	# 	elif i == 3:
	# 		split = shlex.split(line)
	# 		print(split)
	# 		mem = float(split[7]) / float(split[3]) * 100
	# 	i += 1
	# 	if i == 4:
	# 		break
    #
	# if _is_my_info(vm_ip):
	# 	sql = 'update ipdata set cpu = ?, mem = ? where ipadd = ?'
	# 	val = (cpu, mem, vm_ip)
	# 	_exec_sql_by_val(_ipdata, sql, val)
    #
	# else:
	# 	sql = 'insert into ipdata (ipadd, type, cpu, mem) values (?, ?, ?, ?)'
	# 	val = (vm_ip, 2, cpu, mem)
	# 	_exec_sql_by_val(_ipdata, sql, val)

if __name__ == '__main__':
	args = sys.argv
	# print(args)
	ip = args[1]
	vm_ip = args[2]
	vm_port = args[3]
	vm_id = _create_snapshot(ip, vm_ip)
	# print(vm_id)

	command = '/mnt/sh/start {0} {1} {2}'.format(vm_ip, vm_port, vm_id)

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

			_delete_snapshot(vm_id)
			vm_id = _create_snapshot(ip, vm_ip)

			command = '/mnt/sh/start {0} {1} {2}'.format(vm_ip, vm_port, vm_id)
			p = _exec_process(command)

			if _is_start(p):
				break

	# _update_vm_info(vm_ip)
