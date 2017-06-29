import subprocess
from subprocess import PIPE
import shlex
import sys

def _exec_process(command):
	args = shlex.split(command)
	p = subprocess.Popen(args, stdout = PIPE)

	return p

def _is_start(p):
	while True:
		line = p.stdout.readline()
		sys.stdout.write(line)
		if line.count('vm start complete') != 0:
			return True

		elif line.count('already in use') != 0:
			return False

		if not line and p.poll() != None:
			pass

	return False
if __name__ == '__main__':
	args = sys.argv
	vm_id = args[1]
	vm_port = args[2]
	vm_ip = args[3]
	command = '/mnt/sh/migration {0} {1} {2}'.format(vm_id, vm_port, vm_ip)
	p = _exec_process(command)
	if _is_start(p):
		print("migration complete.")
	else:
		print("migration error.")
