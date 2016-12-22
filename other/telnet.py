# 192.168.3.18 telnet

import telnetlib
import sys

HOST = "192.168.3.18"
PORT = 4444
user = "pi"
password = "raspberry"

if __name__ == '__main__':

	port = sys.args[1]

	tn = telnetlib.Telnet(host = HOST, port = PORT)

	tn.write(b"info status\n")

	tn.write(b"migrate_set_speed 1g")

	tn.write(b"migrate -d tcp:192.168.3.17:4449")

	tn.write(b"quit\n")

"""
#!/bin/bash

get_ipaddrs() {
  echo 
  ifconfig -a                                       |
  grep inet[^6]                                     | 
  sed 's/.*inet[^6][^0-9]*\([0-9.]*\)[^0-9]*.*/\1/' | 
  grep -v '^127\.'
}

ip=`get_ipaddrs`

telnet $ip 4444
"""

"""
> info status
VM status: running

> migrate_set_speed 1g

> migrate -d tcp:192.168.3.17:4449

> info migrate
Migration status: active
Migration status: completed
"""