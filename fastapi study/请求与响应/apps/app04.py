from fastapi import APIRouter,Form
from pydantic import BaseModel,Field,validator
from datetime import date
from typing import List,Union

app04= APIRouter()


@app04.post("/regin")
async def regin(username:str = Form(),password:str = Form() ): 
    return {"username":username}