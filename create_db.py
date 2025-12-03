import sqlite3

conn = sqlite3.connect("../database.db")

cur = conn.cursor()

sql_file = open('tables.ddl','r',encoding='UTF-8').read()

for req in sql_file.split(';'):
    cur.execute(req)
conn.commit()

conn.close()
