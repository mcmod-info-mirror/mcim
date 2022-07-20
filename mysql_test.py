import mysql

pwd = "z0z0r4admin"
host = "127.0.0.1"
port = 3306
user = "root"
dbname = "mod_info"

db = mysql.Database(host, port, user, pwd, dbname)
print(db.mysql_version())
print(db.show_tables())