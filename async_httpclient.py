
import asyncio
import aiohttp
import functools

__all__ = [
	'AsyncHTTPClient'
]

def _request_cb_wrapper(url, callback):
	@functools.wraps(callback)
	def wrap(task):
		nonlocal url, callback
		res, content = task.result()
		return callback(url, res, content)
	return wrap

class AsyncHTTPClient:
	'''
	Usage: cli = AsyncHTTPClient()
	'''
	def __init__(self): # limit: int = 64 TODO
		pass

	def new_session(self):
		'''
		Usage:
			async with cli.new_session() as session:
				pass
		'''
		return aiohttp.ClientSession()

	async def get(self, url: str):
		'''
		Usage: res, content = await cli.get('http://example.com')
		'''
		async with self.new_session() as session:
			async with session.get(url) as res:
				content = await res.text()
				return res, content

	async def get_all(self, urls: list[str], callback=None):
		'''
		Usage:
			urls = ['http://example.com', 'http://example2.com']
			responses = await cli.get_all(urls)
			for i, (res, content) in enumerate(responses):
				print('Response for "{}": {} ;Content: {} Byte'.format(urls[i], res.status, len(content)))
		'''
		tasks = []
		for url in urls:
			task = asyncio.create_task(self.get(url))
			if callback is not None:
				task.add_done_callback(_request_cb_wrapper(url, callback))
			tasks.append(task)
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
		def callback(url, res, content):
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
