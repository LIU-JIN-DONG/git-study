from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from apps.app01 import app01
from apps.app02 import app02
from apps.app03 import app03
from apps.app04 import app04
from apps.app05 import app05
from apps.app06 import app06
from apps.app07 import app07
app = FastAPI()

app.mount("/static",StaticFiles(directory="statics")) 

app.include_router(app01,tags=["app01"])
app.include_router(app02,tags=["app02"])
app.include_router(app03,tags=["app03"])
app.include_router(app04,tags=["app04"])
app.include_router(app05,tags=["app05"])
app.include_router(app06,tags=["app06"])
app.include_router(app07,tags=["app07"])




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