from fastapi import APIRouter 
 
app01 = APIRouter()

@app01.get("/user/1")
async def user():
    return {"user_id":"root"}


@app01.get("/user/{id}")
async def user(id):
    return {"user_id":id}

@app01.get("/article/{id}")
async def article(id:int):
    return {"article_id":id}