
import asyncio
import aiohttp

__all__ = [
	'AsyncHTTPClient'
]

class AsyncHTTPClient:
	'''
	Usage: cli = AsyncHTTPClient()
	'''
	def __init__(self): # limit: int = 64 TODO
		pass

	async def new_session(self, headers=None, timeout=None):
		'''
		Usage:
			async with cli.new_session() as session:
				pass
		'''
		return aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=timeout))

	async def get_session(self,headers=None, timeout=None):
		'''
		Usage:
			async with cli.get_session() as session:
				pass
		'''
		return await self.new_session(headers=headers, timeout=timeout)

	async def get(self, url: str, headers=None, timeout=None, sem=None, session=None, *, callback=None):
		'''
		Usage: res, content = await cli.get('http://example.com')
		'''
		if sem is not None:
			async with sem:
				if session is None:
					pass
					async with await self.get_session(headers, timeout=timeout) as session:
						async with session.get(url) as res:
							if callback is not None:
								return await callback(res)
							reader = res.content
							content = await reader.read()
							return res, content
				else:
					pass
					async with session.get(url) as res:
						pass
						if callback is not None:
							return await callback(res)
						reader = res.content
						content = await reader.read()
						return res, content
		else:
			if session is None:
				pass
				async with await self.get_session(headers, timeout=timeout) as session:
					async with session.get(url) as res:
						if callback is not None:
							return await callback(res)
						reader = res.content
						content = await reader.read()
						return res, content
			else:
				pass
				async with session.get(url) as res:
					pass
					if callback is not None:
						return await callback(res)
					reader = res.content
					content = await reader.read()
					return res, content
			# 感觉这个session的判断不好但不知道咋改
			# '''**想不出建议不改 \o/**'''

	async def get_all(self, urls: list[str], headers=None, timeout=None, session=None, sem=None, *, callback=None):
		sem = asyncio.Semaphore(sem)
		'''
		Usage:
			urls = ['http://example.com', 'http://example2.com']
			responses = await cli.get_all(urls)
			for i, (res, content) in enumerate(responses):
				print('Response for "{}": {} ;Content: {} Byte'.format(urls[i], res.status, len(content)))
		'''
		tasks = [asyncio.create_task(self.get(url, headers, timeout=timeout, session=session, sem=sem, callback=callback)) for url in urls]
		print(len(tasks))
		return await asyncio.gather(*tasks)

	# def get_all_sync(self, *args, **kwargs):
	# 	'''
	# 	Usage: responses = cli.get_all_sync(['http://example.com', 'http://www.example2.com'])
	# 	'''
	# 	return asyncio.run(self.get_all(*args, **kwargs))

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
	# Tester.main() #偶尔误触运行了...
	asyncio.run(AsyncHTTPClient().get('https://api.papermc.io/v2/projects',callback=lambda res: print(res.status)))
