#!/usr/bin/python3.5

import subprocess
import os
import telnetlib
import shlex
import sys

user = "pi"
password = "raspberry"

toip = "192.168.3.17"
fromip = "192.168.3.18"

iPipe_r, iPipe_w = os.pipe()


# migrate
print('migrate run... from %s to %s' % (fromip, toip))
ssh_command = "sshpass -p {0} ssh {1}@{2}".format(password, user, fromip)
command = ssh_command + " python /mnt/telnet.py {0}".format(toip)
# command = ssh_command + " ls -la"
# command = command.split(" ")
print(command)
p1 = subprocess.Popen(command, shell=True)


# process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
# out, err = process.communicate(commands.encode('utf-8'))
# print(out.decode('utf-8'))

#clone
# def clone(fromip, toip):
# 	command1 = "/mnt/sh/send_snapshot {}".format(toip)

# 	iPipe_r, iPipe_w = os.pipe()

# 	oSub1 = subprocess.Popen(
# 	    ['sshpass', 'ssh', 'pi@{}'.format(fromip), command1],
# 	    stdout=subprocess.PIPE, stdin=iPipe_r)

# 	os.write(iPipe_w, '{}\n'.format(password).encode())

# 	print(oSub1.stdout.read().decode())

# 	command2 = "/mnt/sh/start"

# 	oSub2 = subprocess.Popen(
# 	    ['sshpass', 'ssh', 'pi@{}'.format(toip), command2],
# 	    stdout=subprocess.PIPE, stdin=iPipe_r)

# 	os.write(iPipe_w, '{}\n'.format(password).encode())

# 	print(oSub2.stdout.read().decode())

# 	print('clone {0} to {1} complete.'.format(fromip, toip))

#migrate
# def migrate(fromip, toip):
# 	print('migrate run... from {0} to {1}'.format(fromip, toip))

# def help():
# 	print('migrate')
# 	print('clone')


# Main
# while 1:

	# print("What do you want to do?")

	# command = input('>> ')

	# commands = command.split()


	# if commands[0] == 'clone':
	# 	if len(commands) == 3:
	# 		clone(commands[1], commands[2])
	# 	else:
	# 		print('error... Put \"clone ip1 ip2\"')

	# elif commands[0] == 'migrate':
	# 	if len(commands) == 3:
	# 		migrate(commands[1], commands[2])
	# 	else:
	# 		print('error... Put \"migrate ip1 ip2\"')

	# elif commands[0] == 'help':
	# 	if len(commands) == 1:
	# 		help()
	# 	else:
	# 		print('error... Put \"help\"')

	# else:
	# 	print('quit')
	# 	break





# print "*subprocess.call"
# result = subprocess.call(command)
# print subprocess.call(command)
# print result
# if result == 0:
# 	print "success"


# print "*subprocess.check_call\n"
# print subprocess.check_call(command)

# print"*subprocess.check_output\n"
# print subprocess.check_output(command)

