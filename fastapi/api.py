from fastapi import FastAPI
import datetime
import curseforge_api
api = FastAPI()

@api.get("/")
async def root():
    return {"message": "z0z0r4 Mod Info"}

@api.get("/curseforge")
async def curseforge():
    pass
    #return curseforge_api.end_point()

@api.get("/curseforge/games")
async def curseforge_games():
    pass
    return curseforge_api.Games().get_all_games()

