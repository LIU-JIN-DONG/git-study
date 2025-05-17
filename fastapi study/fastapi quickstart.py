from fastapi import FastAPI
import uvicorn
from app.app01 import app01
app = FastAPI()

app.include_router(app01,tags=["app01"])

@app.post(
    "/items",
    tags=["这是一个items的测试接口"],
    summary="这是一个items的测试接口",
    description="这是一个items的测试接口",
)
async def home():
    return {"items":"items数据"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)