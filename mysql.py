# 此库正摆烂，拒绝接受请求。

import pymysql

class Database:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        '''
        创建并连接数据库。

        需提供 `host` `port` `user` `password` `database` 。

        `host` : 主机名。

        `port` : 端口。

        `user` : 用户名。

        `password`: 密码。

        `database`: 需操作的数据库。

        用法: db = Database(host, port, user, password, database)
        '''
        self.db = None
        self.connect(host=host, port=port, user=user, password=password, database=database)

    def connect(self, host: str, port: int, user: str, password: str, database: str):
        '''
        重新连接数据库。
        
        需提供 `host` `port` `user` `password` `database` 。

        `host` : 主机名。

        `port` : 端口。

        `user` : 用户名。

        `password`: 密码。

        `database`: 需操作的数据库。

        用法: db.connect(host, port, user, password, database)
        '''
        if self.db is not None:
            self.disconnect()
        self.db = pymysql.connect(host=host, port=port, user=user, password=password, database=database)

    def mysql_version(self) -> str:
        '''
        获取数据库版本。

        用法: version = db.mysql_version()
        '''
        with self.db.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            return cursor.fetchone()

    def delete_table(self, table: str) -> bool :
        '''
        删除整个表。

        需提供可操作数据库的 `table` 。

        `table` : 表。

        如果成功则返回 `True` , 否则返回 `False` 。

        用法: ok = db.delete_table('table_name')
        '''
        with self.db.cursor() as cursor:
            try:
                cursor.execute("DROP TABLE %s", (table, ))
                self.db.commit()
                return True
            except Exception as e:
                print('Exception in Database.delete_table:', type(e), str(e))
                return False
    
    def insert(self, table: str, **kwargs) -> str :
        '''
        用法: db.insert(table, key1=value1, key2=value2, ...)
        '''
        assert len(kwargs) > 0, "No value to insert"
        keys = []
        values = []
        for k, v in kwargs.items():
            keys.append(k)
            values.append(v)
        self.db.begin()
        sql = "INSERT INTO %s ({0}) VALUES ({0})".format(','.join(['%s'] * len(keys)))
        with self.db.cursor() as cursor:
            cursor.execute(sql, (table, *keys, *values))
        self.db.commit()

    def create_table(self, table: str, *args: str):
        '''
        创造一个新表。
        
        用法: db.create_table(table, arg1, arg2, ...)
        '''
        sql = "CREATE TABLE %s ({0}) ENGINE=InnoDB DEFAULT CHARSET=utf8".format(','.join(['%s'] * len(args)))
        with self.db.cursor() as cursor:
            cursor.execute(sql, (table, *args))
        self.db.commit()

    def disconnect(self):
        '''
        断开数据库连接。
        
        用法: db.disconnect()
        '''
        assert self.db is not None, "Database not connected"
        self.db.disconnect()
        self.db = None

    def select(self, table: str):
        '''
        展示表中的数据。

        用法: callback = db.select(table)
        '''
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM " + table)
            return cursor.fetchone()
    
    def show_tables(self):
        '''
        展示所有的表。

        用法: ok = db.show_tables()
        '''
        with self.db.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            return cursor.fetchone()
    
    def delete_database(self, database: str):
        '''
        删库跑路。

        用法: db.delete_database(database)
        '''
        with self.db.cursor() as cursor:
            cursor.execute("DROP DATABASE " + database)
        self.db.commit()
    
    def create_database(self, database: str):
        '''
        开库开搞。

        用法: db.create_database(database)
        '''
        with self.db.cursor() as cursor:
            cursor.execute("CREATE DATABASE " + database)
        self.db.commit()


# pwd = emjYT6NcSi8RKNFc
# host = 10.0.0.20
# port = 3306
# user = mod_api_test
# dbname = mod_api_test
