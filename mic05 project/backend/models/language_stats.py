from tortoise import fields, models
from typing import Dict, Optional, cast, List
from datetime import datetime
from tortoise.contrib.pydantic.creator import pydantic_model_creator
from utils.language_utils import normalize_language_code

class LanguageStats(models.Model):
    '''全局语言使用统计模型'''
    id = fields.IntField(pk=True)
    language = fields.CharField(max_length=10) # 语言代码 如：zh-CN,en-US
    stats = fields.IntField(default=0)  # 语言统计次数 如：100
    last_updated = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "language_stats"
    
    @classmethod
    async def increment_usage(cls,language:str) -> None:
        """增加语言使用次数"""
        lang = normalize_language_code(language)
        stats_record = await cls.filter(language=lang).first()
        if not stats_record:
            stats_record = await cls.create(language=lang,stats=1)
            return
        
        stats_record.stats += 1
        await stats_record.save()

    @classmethod
    async def get_top_language(cls) -> Dict:
        """获取返回最多的语言"""
        stats_record = await cls.all().order_by("-stats").first()
        if not stats_record or not stats_record.stats:
            return {"en-US": 100}
        
        return {stats_record.language: stats_record.stats}

    @classmethod 
    async def get_all_languages(cls) -> List[str]:
        """获取所有语言(按使用频率排序)"""
        stats_record = await cls.all().order_by("-stats")
        if not stats_record:
            return ["en-US","zh-CN"]
        
        return [stats_record.language for stats_record in stats_record]


# 创建Pydantic模型，用于API响应
LanguageStatsPydantic = pydantic_model_creator(LanguageStats, name="LanguageStats")
