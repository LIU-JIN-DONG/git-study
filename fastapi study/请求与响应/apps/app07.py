from fastapi import APIRouter,Form,File,UploadFile,Request
from pydantic import BaseModel,Field,validator,EmailStr
from datetime import date
from typing import List,Union

app07= APIRouter()

class UserInfo(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name : Union[str,None] = None

class UserOut(BaseModel):   
    username: str
    email: EmailStr
    full_name : Union[str,None] = None

@app07.post("/createUser",response_model=UserOut)
async def items(user:UserInfo): 
    return user
 
