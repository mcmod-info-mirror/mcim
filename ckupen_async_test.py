#!/usr/bin/python3

import asyncio
import aiohttp

async def response_get(url):
    print('getting:', url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            content = await res.text()
            return url, res, content

def callback(task):
    url, res, cont = task.result()
    print('result:', url, ':', res.status)

async def main():
    tasks = []
    urls = ["https://www.curseforge.com/minecraft/mc-mods"]
    for url in urls:
        task = asyncio.create_task(response_get(url))
        tasks.append(task)
        task.add_done_callback(callback)
    results = await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
