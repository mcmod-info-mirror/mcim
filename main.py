
import threading
from fastapi import FastAPI
import uvicorn
import asyncio
from apis import *
from config import *
from async_httpclient import *
import webapi
import sync

def main():
    MCIMConfig.load()
    print('Welecome to MCIM')
    webthread = threading.Thread(target=uvicorn.run, args=(webapi.api,), kwargs={"host":"127.0.0.1", "port":8000})
    #syncthread = threading.Thread(target=asyncio.run, args=(sync.main(),), daemon=True)

    webthread.start()
    #syncthread.start()

    webthread.join()
    #syncthread.join()

    print('~~Bye~~')

if __name__ == "__main__":
    main()