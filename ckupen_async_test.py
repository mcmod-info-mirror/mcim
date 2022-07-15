import asyncio
import aiohttp

# DEBUG = True

# if DEBUG:
#     debug = print
# else:
#     def debug(*args, **kwargs):
#         pass

async def get_response(url,method="GET"):
    # debug('getting:', url)
    async with aiohttp.ClientSession() as session:
        async with session.request(method,url) as res:
            return res
    # await asyncio.sleep(0.5) 
    '''
    Windows 下的 asyncio 库有毛病，asyncio.run() 会报错，
    raise RuntimeError('Event loop is closed')
        RuntimeError: Event loop is closed
    虽然加了好像不顶用 见 https://github.com/aio-libs/aiohttp/issues/4324
    '''

def callback(task):
    res = task.result()

async def main(urls):
    tasks = []
    for url in urls:
        task = asyncio.create_task(get_response(url,method="GET"))
        tasks.append(task)
        # task.add_done_callback(callback)
        await asyncio.gather(*tasks)
if __name__ == '__main__':
    a = asyncio.run(main(["https://baidu.com","https://qq.com"]))