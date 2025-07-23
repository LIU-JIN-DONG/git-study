from datetime import datetime
from enum import unique
from typing import Optional,List,Dict, Sequence
from tortoise import fields, models
from tortoise.contrib.pydantic.creator import pydantic_model_creator

class History(models.Model):
    """会话历史记录模型 - 存储整个会话的对话历史"""
    id = fields.IntField(pk=True)
    session_id = fields.CharField(max_length=36,unique=True) # 会话ID
    conversation = fields.JSONField() # 对话内容数组 [{"id": "...", "source_text": "...", "source_language": "...", "target_text": "...", "target_language": "...", "timestamp": "..."}]
    summary = fields.TextField(null=True) # GPT生成的会话总结
    title = fields.CharField(max_length=255,null=True) # 会话标题
    category = fields.CharField(max_length=255,null=True) # 会话分类
    start_time = fields.DatetimeField(auto_now_add=True)
    end_time = fields.DatetimeField(auto_now=True) 
    
    class Meta:
        table = "history"

    @classmethod
    async def create_history(cls,session_id:str,conversation:List[Dict],summary:Optional[str]=None) -> "History":
        """保存会话结束后的完整历史记录"""
        history = await cls.create(
            session_id=session_id,
            conversation=conversation,
            end_time=datetime.now(),
            summary=summary
        )
        return history

    @classmethod
    async def get_by_session_id(cls,session_id:str) -> Optional["History"]:
        """根据会话ID获取历史记录"""
        return await cls.filter(session_id=session_id).first()
    
    @classmethod
    async def get_all_histories(cls,page:int=1,limit:int=20) -> Sequence["History"]:
        """获取所有历史记录"""
        offset = (page - 1)*limit
        return await cls.all().order_by("-start_time").offset(offset).limit(limit).all()

    @classmethod
    async def update_summary(cls,session_id:str,summary:str) -> bool:
        """更新会话总结"""
        session = await cls.get_by_session_id(session_id)
        if not session:
            return False
        
        session.summary = summary
        await session.save()
        return True

    @classmethod
    async def get_by_category(cls,category:str) -> Sequence["History"]:
        """根据会话分类获取历史记录"""
        return await cls.filter(category=category).all()
    

# 创建Pydantic模型，用于API响应
HistoryPydantic = pydantic_model_creator(History, name="History")
