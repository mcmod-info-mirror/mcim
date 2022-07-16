
import asyncio
import aiohttp
import functools

__all__ = [
	'AsyncHTTPClient'
]

class AsyncHTTPClient:
	'''
	Usage: cli = AsyncHTTPClient()
	'''
	def __init__(self): # limit: int = 64 TODO
		pass

	async def new_session(self):
		'''
		Usage:
			async with cli.new_session() as session:
				pass
		'''
		return aiohttp.ClientSession()

	async def get_session(self):
		'''
		Usage:
			async with cli.get_session() as session:
				pass
		'''
		return await self.new_session()

	async def get(self, url: str, *, callback=None):
		'''
		Usage: res, content = await cli.get('http://example.com')
		'''
		async with await self.get_session() as session:
			async with session.get(url) as res:
				if callback is not None:
					return await callback(url, res)
				reader = res.content
				content = await reader.read()
				return res, content

	async def get_all(self, urls: list[str], *, callback=None):
		'''
		Usage:
			urls = ['http://example.com', 'http://example2.com']
			responses = await cli.get_all(urls)
			for i, (res, content) in enumerate(responses):
				print('Response for "{}": {} ;Content: {} Byte'.format(urls[i], res.status, len(content)))
		'''
		tasks = [asyncio.create_task(self.get(url, callback=callback)) for url in urls]
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
