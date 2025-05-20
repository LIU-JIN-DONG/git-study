from fastapi import FastAPI,APIRouter
from tortoise.contrib.fastapi import register_tortoise
import uvicorn
from settings import TORTOISE_ORM
from api.student import student_api

app=FastAPI()
app.include_router(student_api,prefix="/student")

register_tortoise(
    app=app,
    config=TORTOISE_ORM,
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000,reload=True)