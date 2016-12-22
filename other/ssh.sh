#!/bin/bash

if [ $1 -eq "17" ]; then
	echo "ssh pi@192.168.3.17"
	host=192.168.3.17
elif [ $1 -eq "18" ]; then
	echo "ssh pi@192.168.3.18"
	host=192.168.3.18
elif [ $1 -eq "2" ]; then
	echo "ssh pi@192.168.3.2"
	host=192.168.3.2
elif [ $1 -eq "11" ]; then
	echo "ssh pi@192.168.3.11"
	host=192.168.3.11
elif [ $1 -eq "32" ]; then
	echo "ssh pi@192.168.3.32"
	host=192.168.3.32
elif [ $1 -eq "173" ]; then
	echo "ssh pi@192.168.1.173"
	host=192.168.1.173
else
	host="192.168.3."$1
	echo "ssh pi@"$host
# else
# 	echo "arg is '17' or '18'"
# 	exit 1
fi

login_name=pi
password=raspberry

sshpass -p $password ssh $login_name@$host

# expect -c "
# set timeout -1
# spawn ssh -l $login_name $host
# expect \"Are you sure you want to continue connecting (yes/no)?\" {
#     send \"yes\n\"
#     expect \"$login_name@$host's password:\"
#     send \"$password\n\"
# } \"$login_name@$host's password:\" {
#     send \"$password\n\"
# } \"Permission denied (publickey,gssapi-keyex,gssapi-with-mic).\" {
#     exit
# }
# interact
# "
