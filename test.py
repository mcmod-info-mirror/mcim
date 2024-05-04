# from app.sync.modrinth import *
# from app.sync.curseforge import *
# check_alive.send()

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
import asyncio

app = FastAPI()

@app.get("/")
async def read_root():
    return RedirectResponse(url="https://api.curseforge.com/v1/mods/1", headers={"x-api-key": "$2a$10$2DOXBr1x82Acn1A6GGw5b.psdLVOo29u5gEahTQSiGYmDOp2QXFSu"})