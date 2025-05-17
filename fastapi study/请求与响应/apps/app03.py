from fastapi import APIRouter
from pydantic import BaseModel,Field,validator
from datetime import date
from typing import List,Union
app03= APIRouter()

class Address(BaseModel):
    province:str
    city:str

class User(BaseModel):
    name: str = 'root'
    age: int =  Field(default=0,gt=0,lt=100)
    birth: Union[date,None] = Field(default=None)
    friends: List[int]=[]
    addr:Address

    @validator('name')
    def name_must_alpha(cls,value):
        assert value.isalpha(),'name must be alphabetic'
        return value

@app03.post("/user")
async def user(user:User ): 
    return user