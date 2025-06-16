from tortoise import fields
from tortoise.models import Model
from datetime import datetime

class TranslationRecord(Model):
    id = fields.BigIntField(pk=True)
    translation_id = fields.CharField(max_length=255,unique=True)
    user_id = fields.CharField(max_length=255,null=True)
    device_id = fields.CharField(max_length=255,null=True,default="default")
    source_language = fields.CharField(max_length=50)
    target_language = fields.CharField(max_length=50)
    source_text = fields.TextField()
    translated_text = fields.TextField()
    original_audio_url = fields.CharField(max_length=500,null=True)
    tts_audio_url = fields.CharField(max_length=500,null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "translation_records"
        indexes =[
            ("device_id","created_at"),
            ("source_language",),
            ("target_language",),
            ]
