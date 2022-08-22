import asyncio
import aiohttp

__all__ = [
    'AsyncHTTPClient'
]


class AsyncHTTPClient:
    '''
	Usage: cli = AsyncHTTPClient()
	'''

    def __init__(self, **kwargs):
        self._lock = asyncio.Lock()
        self._session = None
        self._session_kwargs = kwargs
        self._context_count = 0

    @property
    def session(self):
        assert self._session is not None, "You are not in a context"
        return self._session

    async def __aenter__(self):
        async with self._lock:
            if self._session is None:
                self._session = await self.new_session()
            self._context_count += 1
        return self

    async def __aexit__(self, etyp, eval, traceback):
        async with self._lock:
            self._context_count -= 1
            if self._context_count == 0:
                await self._session.close()
                self._session = None
                await asyncio.sleep(0)
        return False

    def format_params(self, kwargs):
        if "params" in kwargs:
            if not kwargs["params"] is None:
                params = kwargs["params"]
                final_params = params.copy()
                for param in params:
                    if params[param] is None:
                        del final_params[param]
                kwargs["params"] = final_params
        return kwargs

    async def new_session(self, **kwargs):
        '''
		Usage:
			async with await cli.new_session() as session:
				pass
		'''
        return aiohttp.ClientSession(**{**self._session_kwargs, **kwargs})

    async def _get(self, url: str, /, *, callback=None, **kwargs):
        async with self.session.get(url, **kwargs) as res:
            if callback is not None:
                return await callback(res)
            reader = res.content
            content = await reader.read()
            return res, content

    async def get(self, url: str, /, *, callback=None, sem=None, **kwargs):
        '''
		Usage: res, content = await cli.get('http://example.com')
		'''

        # aiohttp 不支持自动忽略 param 为 None 的参数
        # if "params" in kwargs:
        #     if not kwargs["params"] is None:
        #         params = kwargs["params"]
        #         final_params = params.copy()
        #         for param in params:
        #             if params[param] is None:
        #                 del final_params[param]
        #         kwargs["params"] = final_params
        kwargs = self.format_params(kwargs)

        if sem is None:
            return await self._get(url, callback=callback, **kwargs)
        async with sem:
            return await self._get(url, callback=callback, **kwargs)

    async def _post(self, url: str, /, *, callback=None, **kwargs):
        async with self.session.post(url, **kwargs) as res:
            if callback is not None:
                return await callback(res)
            reader = res.content
            content = await reader.read()
            return res, content
    
    async def post(self, url: str, /, *, callback=None, sem=None, **kwargs):
        '''
        Usage: res, content = await cli.post('http://example.com', data={'key': 'value'})
        '''
        kwargs = self.format_params(kwargs)

        #_get()通用
        if sem is None:
            return await self._post(url, callback=callback, **kwargs)
        async with sem:
            return await self._post(url, callback=callback, **kwargs)

    async def get_all(self, urls: list[str], *, limit: int = -1, callback=None, **kwargs):
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

        async def runner():
            async with self:
                return await self.get_all(*args, **kwargs)

        return asyncio.run(runner())


class Tester:
    def __init__(self):
        self.cli = AsyncHTTPClient()
        self.target = ['https://google.com', 'https://github.com']

    async def test_get(self):
        url = self.target[0]
        async with self.cli:
            for url in self.target:
                res, content = await self.cli.get(url)
                print('Response for "{}": {} ;Content: {} Byte'.format(url, res.status, len(content)))

    async def test_get_all(self):
        async with self.cli:
            responses = await self.cli.get_all(self.target)
        for i, (res, content) in enumerate(responses):
            url = self.target[i]
            print('Response for "{}": {} ;Content: {} Byte'.format(url, res.status, len(content)))

    async def test_get_all_with_callback(self):
        async def callback(res):
            content = await res.content.read()
            print('Response for "{}": {} ;Content: {} Byte'.format(res.url, res.status, len(content)))

        async with self.cli:
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
        print('=> Testing AsyncHTTPClient.get')
        asyncio.run(tester.test_get())
        print('=> Testing AsyncHTTPClient.get_all')
        asyncio.run(tester.test_get_all())
        print('=> Testing AsyncHTTPClient.get_all with callback')
        asyncio.run(tester.test_get_all_with_callback())
        print('=> Testing AsyncHTTPClient.get_all_sync')
        tester.test_get_all_sync()


if __name__ == '__main__':
    Tester.main()
