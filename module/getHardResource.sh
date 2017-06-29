#!/bin/bash

sshpass -p raspberry ssh -o StrictHostKeyChecking=no pi@192.10.1.10 /home/pi/sh/mount 192.10.1.15
sshpass -p raspberry ssh -o StrictHostKeyChecking=no pi@192.10.1.10 python /mnt/py/getHardInfo.py &
sshpass -p raspberry ssh -o StrictHostKeyChecking=no pi@192.10.1.10 python /home/pi/getResourceText.py &
sshpass -p raspberry ssh -o StrictHostKeyChecking=no pi@192.20.1.10 /home/pi/sh/mount 192.20.1.15
sshpass -p raspberry ssh -o StrictHostKeyChecking=no pi@192.20.1.10 python /mnt/py/getHardInfo.py &
sshpass -p raspberry ssh -o StrictHostKeyChecking=no pi@192.20.1.10 python /home/pi/getResourceText.py &
