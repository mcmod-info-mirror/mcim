
import threading

from .database import DataBase

__all__ = [
	'DBPoolItem',
	'DBPool'
]

class DBPoolItem: pass
class DBPool: pass

class DBPoolItem:
	def __init__(self, pool: DBPool, db: DataBase):
		self.pool = pool
		self.db = db

	def put(self):
		assert self.db is not None
		self.pool._put_conn(self.db)
		self.db = None

	def __enter__(self) -> DataBase:
		assert self.db is not None
		self.db.__enter__()
		return self.db

	def __exit__(self, etyp, err, traceback):
		res = self.db.__exit__(etyp, err, traceback)
		self.put()
		return res

class DBPool:
	def __init__(self, kwargs: dict, size: int = 32):
		self._cond = threading.Condition(threading.Lock())
		self._size = size
		self._kwargs = kwargs
		self._conns = [DBPoolItem(self, DataBase(**self._kwargs)) for _ in range(self._size)]

	@property
	def size(self) -> int:
		return self._size

	@property
	def remain(self) -> int:
		return len(self._conns)

	@property
	def isempty(self) -> bool:
		return self.remain == 0

	def get(self) -> DBPoolItem:
		conn: DataBase
		with self._cond:
			if len(self._conns) == 0:
				self._cond.wait()
			conn = self._conns.pop()
		return conn

	def _put_conn(self, conn: DataBase):
		assert isinstance(conn, DataBase)
		with self._cond:
			self._conns.append(conn)
			self._cond.notify()
