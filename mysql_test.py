from apis import mysql

pwd = "z0z0r4admin"
host = "127.0.0.1"
port = 3306
user = "root"
dbname = "mod_info"

db = mysql.DataBase(host, port, user, pwd, dbname)

def save_json_to_mysql(table, **kwargs):
    db.insert(table=table, **kwargs)

save_json_to_mysql(table="mod_status",modid=1,status=404)

# print(db.mysql_version())
# # print(db.create_table("mod_info", "`modid` INT", "`data` json"))
# print(db.update("mod_info",updates={"data": "'{\"a\":1}'"},where_keys={"modid": "3"}))