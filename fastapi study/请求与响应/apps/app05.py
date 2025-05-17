from fastapi import APIRouter,Form,File,UploadFile
from pydantic import BaseModel,Field,validator
from datetime import date
from typing import List,Union

app05= APIRouter()


@app05.post("/file")
async def file(file:bytes = File()): 
    return {"file":len(file)}

@app05.post("/files")
async def files(files:List[bytes] = File()): 
    return {"file":len(files)}

@app05.post("/uploadFile")
async def uploadfile(file:UploadFile): 
    return {"file":file.filename}