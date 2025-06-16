from fastapi import APIRouter
from models.todo import Todo,TodoStatus
from typing import Optional
from pydantic import BaseModel

todos_router=APIRouter()

class TodoRequest(BaseModel):
    device_id:Optional[str]='default'
    description:Optional[str]=None
    status:Optional[TodoStatus] = None

@todos_router.get("/")
async def get_todos():
    todos = await Todo.all()
    return {
        "success":True,
        "data":todos,
        "message":"获取待办事项成功"
    }

@todos_router.get("/{device_id}")
async def get_todos_by_device_id(device_id:Optional[str]='default',limit:int=20):
    todos = await (Todo.filter(device_id=device_id)
                   .order_by("-created_time")
                   .limit(limit))
    if not todos:
        return{
        "success":False,
        "data":[],
        "message":"没有找到待办事项，请检查设备ID"
    }
    return{
        "success":True,
        "data":todos,
        "message":"获取待办事项成功"
    }

@todos_router.post("/")
async def create_todo(todo:TodoRequest):
    new_todo = await Todo.create(**todo.model_dump())
    return{
        "success":True,
        "data":new_todo,
        "message":"创建待办事项成功"
    }

@todos_router.put("/{todo_id}")
async def update_todo(todo_id:str,data:TodoRequest):
    todo = await Todo.filter(id=todo_id).first()
    if not todo:
        return{
            "success":False,
            "message":"待办事项不存在"
        }
    if data.device_id is not None:
        todo.device_id = data.device_id
    if data.description is not None:
        todo.description = data.description
    if data.status is not None:
        todo.status = data.status
    await todo.save()
    return{
        "success":True,
        "data":todo,
        "message":"更新待办事项成功"
    }

@todos_router.delete("/{todo_id}")
async def delete_todo(todo_id:str):
    delete_count=await Todo.filter(id=todo_id).delete()
    if not delete_count:
        return {
            "success":False,
            "message":"待办事项不存在"
        }
    return {
        "success":True,
        "message":"删除待办事项成功"
    }
