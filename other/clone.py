import os
import subprocess

fromip = "192.168.3.18"
toip = "192.168.3.17"

command1 = "/mnt/sh/send_snapshot {}".format(toip)

iPipe_r, iPipe_w = os.pipe()

oSub1 = subprocess.Popen(
    ['sshpass', 'ssh', 'pi@{}'.format(fromip), command1],
    stdout=subprocess.PIPE, stdin=iPipe_r)

sPasswd = "raspberry"
os.write(iPipe_w, '{}\n'.format(sPasswd).encode())

print(oSub1.stdout.read().decode())

command2 = "ls -la"

oSub2 = subprocess.Popen(
    ['sshpass', 'ssh', 'pi@{}'.format(toip), command2],
    stdout=subprocess.PIPE, stdin=iPipe_r)

sPasswd = "raspberry"
os.write(iPipe_w, '{}\n'.format(sPasswd).encode())

print(oSub2.stdout.read().decode())