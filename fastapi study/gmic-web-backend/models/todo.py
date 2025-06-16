from tortoise import fields
from tortoise.models import Model
from enum import Enum
from datetime import datetime

class TodoStatus(str,Enum):
    OPEN = "open"
    DONE = "done"

class Todo(Model):
    id = fields.BigIntField(pk=True)
    device_id = fields.CharField(max_length=255,default="default",null=True)
    description = fields.TextField(description="待办事项描述",null=True)
    status = fields.CharEnumField(enum_type=TodoStatus,default=TodoStatus.OPEN,null=True)
    created_time = fields.DatetimeField(auto_now_add=True)
    modified_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "todos"
        indexes =[
            ("device_id","status"),
            ("device_id","created_time"),
            ("device_id","modified_time"),
            ("status",),
        ]
