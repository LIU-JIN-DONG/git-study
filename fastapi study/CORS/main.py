from fastapi import FastAPI
import time
import uvicorn
from fastapi import Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# @app.middleware("http")
# async def CORSMiddleware(request:Request,call_next):
#     response=await call_next(response)
#     response.headers["Access-Control-Allow-Origin"]="*"
#     return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get('/user')
async def get_user():
    time.sleep(3)
    print("get_user运行")
    return {
        "user":"hamilton"
    }

@app.get("/item/{item_id}")
async def get_item(item_id:int):
    time.sleep(2)
    print(f"get_item运行，item_id={item_id}")
    return {
        "item_id":item_id
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000,reload=True)