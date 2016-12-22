#!/bin/bash

ip="192.168.3."$1

sshpass -p raspberry ssh -o StrictHostKeyChecking=no pi@${ip}