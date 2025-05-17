from fastapi import APIRouter,Form,File,UploadFile,Request
from pydantic import BaseModel,Field,validator
from datetime import date
from typing import List,Union

app06= APIRouter()


@app06.post("/items")
async def items(request:Request): 
    return {
        "Url":request.url,
        "ip":request.client.host,
        "suze":request.headers.get("user-agent"),
        "cookie":request.cookies
        }
 
