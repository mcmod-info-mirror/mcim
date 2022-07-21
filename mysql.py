# 此库正摆烂，拒绝接受请求。

import functools
import pymysql

class DataBase:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        '''
        创建并连接数据库。

        需提供 `host` `port` `user` `password` `database` 。

        `host` : 主机名。

        `port` : 端口。

        `user` : 用户名。

        `password`: 密码。

        `database`: 需操作的数据库。

        用法: db = DataBase(host, port, user, password, database)
        '''
        self.db = None
        self.connect(host=host, port=port, user=user, password=password, database=database)

    def __enter__(self):
        assert self.db is not None, "Database not connected"
        self.db.begin()
        return self

    def __exit__(self, etyp, eval, traceback):
        if etyp is None:
            self.db.commit()
            return True
        self.db.rollback()
        return False

    @staticmethod
    def with_wrapper(callback):
        @functools.wraps(callback)
        def w(self, *args, **kwargs):
            with self:
                return callback(*args, **kwargs)
        return w

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

    def disconnect(self):
        '''
        断开数据库连接。
        
        用法: db.disconnect()
        '''
        assert self.db is not None, "DataBase not connected"
        self.db.disconnect()
        self.db = None

    def mysql_version(self) -> str:
        '''
        获取数据库版本。

        用法: version = db.mysql_version()
        '''
        sql = "SELECT VERSION()"
        with self.db.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchone()

    def select(self, table: str, keys: list[str]):
        '''
        展示表中的数据。

        用法: callback = db.select(table)
        '''
        sql = "SELECT {keys} FROM {table}".\
            format(table=table, keys=','.join(f'`{k}`' for k in keys))
        with self.db.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchone()

    @with_wrapper
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
        sql = "INSERT INTO {table} ({keys}) VALUES ({values})".\
            format(table=table, keys=','.join(f'`{k}`' for k in keys), values=','.join(['%s'] * len(values)))
        with self.db.cursor() as cursor:
            cursor.execute(sql, values)

    @with_wrapper
    def create_table(self, table: str, *args: str):
        '''
        创造一个新表。
        
        用法: db.create_table(table, arg1, arg2, ...)
        '''
        sql = "CREATE TABLE {table} ({args}) ENGINE=InnoDB DEFAULT CHARSET=utf8".\
            format(table=table, args=','.join(args))
        with self.db.cursor() as cursor:
            cursor.execute(sql)

    def delete_table(self, table: str) -> bool :
        '''
        删除整个表。

        需提供可操作数据库的 `table` 。

        `table` : 表。

        如果成功则返回 `True` , 否则返回 `False` 。

        用法: ok = db.delete_table('table_name')
        '''
        sql = "DROP TABLE {table}".\
            format(table=table)
        try:
            with self:
                with self.db.cursor() as cursor:
                    cursor.execute(sql)
            return True
        except Exception as e:
            print('Exception in DataBase.delete_table:', type(e), str(e))
            return False

    # def show_tables(self):
    #     '''
    #     展示所有的表。

    #     用法: ok = db.show_tables()
    #     '''
    #     with self.db.cursor() as cursor:
    #         cursor.execute("SHOW TABLES")
    #         return cursor.fetchone()

    # def delete_database(self, database: str):
    #     '''
    #     删库跑路。

    #     用法: db.delete_database(database)
    #     '''
    #     with self.db.cursor() as cursor:
    #         cursor.execute("DROP DATABASE " + database)
    #     self.db.commit()

    # def create_database(self, database: str):
    #     '''
    #     开库开搞。

    #     用法: db.create_database(database)
    #     '''
    #     with self.db.cursor() as cursor:
    #         cursor.execute("CREATE DATABASE " + database)
    #     self.db.commit()
