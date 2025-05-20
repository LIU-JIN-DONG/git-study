from fastapi import APIRouter
from models import *
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel,validator
from typing import List
from fastapi import HTTPException

student_api=APIRouter()

@student_api.get("/")
async def getAllStudent():
    students  = await Student.all().values("name","clas__name","courses__name")
    student = await Student.filter(sno__gt=202201).values()
    ham =  await Student.get(name="hamilton")
    courses =await ham.courses.all().values("name")
    return {
        "学生":students,
        "ham":await ham.clas.values("name"),
        "ham's courses": await ham.courses.all().values("name","teacher__name")
    }

@student_api.get("/index.html")
async def getHtml(request:Request):
    templates = Jinja2Templates(directory="templates")
    students  = await Student.all()
    return templates.TemplateResponse("index.html",{ 
        "request":request,
        "students":students
    })


class StudentIn(BaseModel):
    name : str
    pwd : str
    sno :int
    clas_id :int
    courses :List[int] = []
    @validator("name")
    def check_name(cls,v):
        assert v.isalpha(),"姓名必须由字母组成"
        return v

    @validator("sno")
    def check_sno(cls,v):
        assert v>202200,"学号必须大于202200"
        return v 

@student_api.post("/")
async def addStudent(student:StudentIn):
    stu= await Student.create(
        name=student.name,
        pwd=student.pwd,
        sno=student.sno,
        clas_id=student.clas_id,
    )

    courses = await Course.filter(id__in=student.courses)
    await stu.courses.add(*courses)
    return {
        "message":"添加学生成功"
    }

@student_api.get("/{id}")
async def getStudent(id:int):
    student = await Student.get(id=id)
    return {
       f"id为{id}的学生":student
    }

@student_api.put("/{id}")
async def updateStudent(id:int,student:StudentIn):
    data = student.dict()
    courses = data.pop("courses")
    stu = await Student.filter(id=id).update(**data)


    edit_stu = await Student.get(id=id)
    choosed_courses = await Course.filter(id__in=courses)
    await edit_stu.courses.clear()
    await edit_stu.courses.add(*choosed_courses)
    return edit_stu

@student_api.delete("/{id}")
async def deleteStudent(id:int):
    deleteCount = await Student.filter(id=id).delete()
    if not deleteCount:
        raise HTTPException(status_code=404,detail="学生不存在")
    return f"删除id={id}的学生"

