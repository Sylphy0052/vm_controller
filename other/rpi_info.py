# user:pi
# password:raspberry

# -*- coding: utf-8

import sqlite3
import os.path

dbname = './ipdata.db'

if not os.path.isfile(dbname):
	conn = sqlite3.connect(dbname)
	c = conn.cursor()

	print("db not exist")
	create_table =  'create table ipdata (ipadd, type, cpu, mem)'
	c.execute(create_table)

else:
	conn = sqlite3.connect(dbname)
	c = conn.cursor()


# テーブル作成
# create_table =  u'''
# create table ipdata (
# ipadd text, type integer, cpu read, mem real
# )
# '''


sql = 'insert into ipdata (ipadd, type, cpu, mem) values (?, ?, ?, ?)'
val = ('192.168.3.2', 1, 10.5, 81.2)
c.execute(sql, val)

conn.commit()

sql = 'select * from ipdata'
for row in c.execute(sql):
	print(row)

conn.close()

"""
# executeメソッドでSQL文を実行する
create_table = '''create table users (id int, name varchar(64),
                  age int, gender varchar(32))'''
c.execute(create_table)

# SQL文に値をセットする場合は，Pythonのformatメソッドなどは使わずに，
# セットしたい場所に?を記述し，executeメソッドの第2引数に?に当てはめる値を
# タプルで渡す．
sql = 'insert into users (id, name, age, gender) values (?,?,?,?)'
user = (1, 'Taro', 20, 'male')
c.execute(sql, user)

# 一度に複数のSQL文を実行したいときは，タプルのリストを作成した上で
# executemanyメソッドを実行する
insert_sql = 'insert into users (id, name, age, gender) values (?,?,?,?)'
users = [
    (2, 'Shota', 54, 'male'),
    (3, 'Nana', 40, 'female'),
    (4, 'Tooru', 78, 'male'),
    (5, 'Saki', 31, 'female')
]
c.executemany(insert_sql, users)
conn.commit()

select_sql = 'select * from users'
for row in c.execute(select_sql):
    print(row)
"""