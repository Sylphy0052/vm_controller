# user:pi
# password:raspberry

# -*- coding: utf-8

import sqlite3
import os.path

dbname = '/mnt/vmdata.db'

if __name__ == '__main__':

	if not os.path.isfile(dbname):
		conn = sqlite3.connect(dbname)
		c = conn.cursor()

		print("db not exist")
		create_table =  'create table vmdata (ipadd, vmname, vmip)'
		c.execute(create_table)

	else:
		conn = sqlite3.connect(dbname)
		c = conn.cursor()

	sql = 'insert into vmdata (ipadd, vmname, vmip) values (?, ?, ?)'
	val = ('192.168.3.2', "vm1", "192.168.3.101")
	c.execute(sql, val)

	conn.commit()

	# sql = 'select * from vmdata'
	# for row in c.execute(sql):
	# 	print(row)

	conn.close()
