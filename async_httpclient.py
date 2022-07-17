
import asyncio
import aiohttp

__all__ = [
	'AsyncHTTPClient'
]

class AsyncHTTPClient:
	'''
	Usage: cli = AsyncHTTPClient()
	'''
	def __init__(self, **kwargs): # limit: int = 64 TODO
		self._session = None
		self._session_kwargs = kwargs

	@property
	def session(self):
		return self._session

	async def new_session(self, **kwargs):
		'''
		Usage:
			async with await cli.new_session() as session:
				pass
		'''
		return aiohttp.ClientSession(**{**self._session_kwargs, **kwargs})

	async def get_session(self, **kwargs):
		'''
		Usage:
			session = await cli.get_session()
		'''
		if self._session is None:
			self._session = await self.new_session(**kwargs)
		return self._session

	async def get(self, url: str, /, *, callback=None, **kwargs):
		'''
		Usage: res, content = await cli.get('http://example.com')
		'''
		async with await self.get_session() as session:
			async with session.get(url, **kwargs) as res:
				if callback is not None:
					return await callback(res)
				reader = res.content
				content = await reader.read()
				return res, content

	async def get_all(self, urls: list[str], *, limit: int=-1, callback=None, **kwargs):
		if limit > 0:
			kwargs['sem'] = asyncio.Semaphore(limit)
		'''
		Usage:
			urls = ['http://example.com', 'http://example2.com']
			responses = await cli.get_all(urls)
			for i, (res, content) in enumerate(responses):
				print('Response for "{}": {} ;Content: {} Byte'.format(urls[i], res.status, len(content)))
		'''
		tasks = [asyncio.create_task(self.get(url, callback=callback, **kwargs)) for url in urls]
		return await asyncio.gather(*tasks)

	def get_all_sync(self, *args, **kwargs):
		'''
		Usage: responses = cli.get_all_sync(['http://example.com', 'http://www.example2.com'])
		'''
		return asyncio.run(self.get_all(*args, **kwargs))

class Tester:
	def __init__(self):
		self.cli = AsyncHTTPClient()
		self.target = ['https://google.com', 'https://github.com']

	async def test_get_all(self):
		responses = await self.cli.get_all(self.target)
		for i, (res, content) in enumerate(responses):
			url = self.target[i]
			print('Response for "{}": {} ;Content: {} Byte'.format(url, res.status, len(content)))

	async def test_get_all_with_callback(self):
		async def callback(url, res):
			content = await res.content.read()
			print('Response for "{}": {} ;Content: {} Byte'.format(url, res.status, len(content)))
		await self.cli.get_all(self.target, callback=callback)

	def test_get_all_sync(self):
		responses = self.cli.get_all_sync(self.target)
		for i, (res, content) in enumerate(responses):
			url = self.target[i]
			print('Response for "{}": {} ;Content: {} Byte'.format(url, res.status, len(content)))

	@classmethod
	def main(cls):
		print('==> Testing AsyncHTTPClient')
		tester = cls()
		print('=> Testing AsyncHTTPClient.get_all')
		asyncio.run(tester.test_get_all())
		print('=> Testing AsyncHTTPClient.get_all with callback')
		asyncio.run(tester.test_get_all_with_callback())
		print('=> Testing AsyncHTTPClient.get_all_sync')
		tester.test_get_all_sync()

if __name__ == '__main__':
	Tester.main()
