from tortoise import Tortoise,fields
from tortoise.models import Model

class Student(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32,description="姓名")
    pwd = fields.CharField(max_length=32,description="密码")
    sno = fields.IntField(description="学号")

    # 一对多
    clas = fields.ForeignKeyField("models.Clas",related_name="students")

    # 多对多
    courses = fields.ManyToManyField("models.Course",related_name="students")

class Course(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32,description="课程名")
    teacher = fields.ForeignKeyField("models.Teacher",related_name="courses")
    addr = fields.CharField(max_length=32,description="地址",default="")

class Clas(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32,description="班级名")

class Teacher(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32,description="教师名")
    pwd = fields.CharField(max_length=32,description="密码")
    tno = fields.IntField(description="教师号")








    