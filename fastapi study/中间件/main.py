from fastapi import FastAPI
import time
import uvicorn
from fastapi import Request
from fastapi.responses import Response


app = FastAPI()

@app.middleware("http")
async def m2(request:Request,call_next):
    #请求中间件
    print("m2 request")
    if request.url.path in ['/user']:
        return Response(content="visit forbidden")

    start = time.time()
    response = await call_next(request)
    #响应中间件
    print("m2 response")
    end = time.time()
    response.headers["ProcessTimer"] = str(end-start)
    return response
    
@app.middleware("http")
async def m1(request:Request,call_next):
    #请求中间件
    print("m1 request")
    response = await call_next(request)
    #响应中间件
    print("m1 response")
    return response
    


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