
import functools
import pymysql

from .command import *

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

	def connect(self, *, host: str, port: int, user: str, password: str, database: str):
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

	def version(self) -> str:
		'''
		获取数据库版本。

		用法: version = db.version()
		'''
		sql = "SELECT VERSION()"
		with self.db.cursor() as cursor:
			cursor.execute(sql)
			return cursor.fetchone()

	def cursor(self):
		return self.db.cursor()

	def execute(self, cmd: CommandBuilder, /, cursor=None):
		if cursor is None:
			return cursor.execute(cmd.command, cmd.values)
		with self.cursor() as cursor:
			return cursor.execute(cmd.command, cmd.values)

	exe = execute
