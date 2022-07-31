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
    p1 = threading.Thread(target=uvicorn.run,args=(webapi.api,),kwargs={"host":"127.0.0.1","port":8000})
    p1.daemon = True
    #p2 = threading.Thread(target=asyncio.run,args=(sync.main(),))
    #p2.daemon = True
    
    p1.start()
    #p2.start()

    p1.join()
    #p2.join()
    print('Bye')
if __name__ == "__main__":
    main()