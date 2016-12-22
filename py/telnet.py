import telnetlib
import sys

def telnet_connection(to_host, telnet_port):
	tn = telnetlib.Telnet("localhost", telnet_port)

	result1 = tn.read_until(b"QEMU", 3)

	print("info status")
	tn.write(b"info status\n")

	result2 = tn.read_until(b'QEMU', 3)
	print(result2.decode('ascii'))


	print("set speed 1g")
	tn.write(b"migrate_set_speed 1g\n")

	result3 = tn.read_until(b'QEMU', 3)
	print(result3.decode('ascii'))


	print("migrate {0}".format(to_host))
	command = "migrate -d tcp:{0}:4449\n".format(to_host)
	tn.write(command.encode('ascii'))

	result4 = tn.read_until(b'QEMU', 3)
	print(result4.decode('ascii'))

	while True:
		print("info migrate")
		tn.write(b"info migrate\n")

		result5 = tn.read_until(b'QEMU', 3).decode('ascii')

		if result5.find('failed') > -1:
			print("migration failed...")
			sys.exit()
		elif result5.find('completed') > -1:
			print("migration success!!")
			break
		else:
			print("migration active.Please wait.")

	print("quit")
	tn.write(b"quit\n")

if __name__ == '__main__':
	to_host = sys.argv[1]
	telnet_port = sys.argv[2]
	telnet_connection(to_host, telnet_port)
