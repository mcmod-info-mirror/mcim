import mysql

pwd = "emjYT6NcSi8RKNFc"
host = "10.0.0.20"
port = 3306
user = "mod_api_test"
dbname = "mod_api_test"

db = mysql.Database(host, port, user, pwd, dbname)
print(db.mysql_version())
print(db.show_tables())
# db.disconnect()
