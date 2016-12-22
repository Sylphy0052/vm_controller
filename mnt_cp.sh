#!/bin/bash

rm -rf /opt/nfs/py /opt/nfs/sh

cp -rf py sh /opt/nfs

# expect -c "
# spawn sudo cp -rf py sh /opt/nfs
# expect \"pass\"
# send \"kento0531\n\"
# interact
# "