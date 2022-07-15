import asyncio
import aiohttp

#loop = asyncio.get_event_loop()
#tasks = [hello(), hello()]
#loop.run_until_complete(asyncio.wait(tasks))
#loop.close()

class Async_request:
    def __init__(self) -> None:
        pass

    async def response_get(self,url):
        async with aiohttp.ClientSession(timeout=60) as session:
            async with session.get(url) as response:
                return response

    def request(self,urls):
        tasks = []
        results = []

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for url in urls:
            task = asyncio.create_task(self.response_get(url))
            tasks.append(task)

        a = loop.run_until_complete(asyncio.wait(tasks))
        
        for t in a[0]:
            results.append(t.result())
        
        return results

# if __name__ == "__main__":
#     reps = async_request.request(["https://qq.com", "https://baidu.com"])