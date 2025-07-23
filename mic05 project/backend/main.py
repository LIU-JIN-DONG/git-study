from atexit import register
from sys import prefix
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
import uvicorn

from config.database import TORTOISE_ORM
from api.websocket_routes import ws_router
from api.http_routes import translate_router

app = FastAPI()
# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)
app.include_router(translate_router,prefix="/api")

register_tortoise(
    app=app,
    config = TORTOISE_ORM,
)
if __name__ =="__main__":
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)
