from fastapi import FastAPI
from routes.translation import translation_router
from routes.todos import todos_router
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from core.settings import TORTOISE_ORM

app = FastAPI(prefix="/api")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(translation_router,prefix="/translation")
app.include_router(todos_router,prefix="/todos")

register_tortoise(
    app=app,
    config=TORTOISE_ORM,
    # generate_schemas=True,
)

if __name__ == "__main__":
    uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)