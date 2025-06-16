from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from models.translate import TranslationRecord
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import aiofiles
from datetime import datetime
from pathlib import Path

translation_router=APIRouter()

# 配置文件存储路径
UPLOAD_DIRECTORY = Path("uploads/audio")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

class TranslationRequest(BaseModel):
    originalText:str
    translatedText:str
    source_language:str
    target_language:str
    device_id:Optional[str]="default"
    original_audio_url:Optional[str]=None
    tts_audio_url:Optional[str]=None


@translation_router.get("/")
async def get_translation():
    translation_records=await TranslationRecord.all()
    return translation_records

@translation_router.get("/history")
async def get_translation_by_device_id(device_id:Optional[str]="default",limit:int = 20):
    translation_records = await (TranslationRecord.filter(device_id=device_id)
                                 .order_by("-created_at")
                                 .limit(limit))
    if not translation_records:
        return {
            "success":False,
            "message":"No translation records found",
            "data":[]
        }
    return {
        "success":True,
        "message":"Translation fetched successfully",
        "data":translation_records
    }

@translation_router.post("/")
async def create_translation(data:TranslationRequest):
    translation_id=str(uuid.uuid4())
    translation_record=await TranslationRecord.create(
        translation_id=translation_id,
        device_id=data.device_id,
        source_language=data.source_language,
        target_language=data.target_language,
        source_text=data.originalText,
        translated_text=data.translatedText,
        original_audio_url=data.original_audio_url,
        tts_audio_url=data.tts_audio_url,
    )
    return {
        "success":True,
        "message":"Translation created successfully",
    }

@translation_router.put("/{translation_id}")
async def update_translation(translation_id:str,data:TranslationRequest):
    old_translation = await TranslationRecord.filter(translation_id=translation_id).first()
    if not old_translation:
        return {
            "success":False,
            "message":"Translation not found",
        }
    
    # 修改模型实例的属性
    old_translation.device_id = data.device_id or "default"
    old_translation.source_language = data.source_language
    old_translation.target_language = data.target_language
    old_translation.source_text = data.originalText
    old_translation.translated_text = data.translatedText
    if data.original_audio_url is not None:
        old_translation.original_audio_url = data.original_audio_url
    if data.tts_audio_url is not None:
        old_translation.tts_audio_url = data.tts_audio_url
    
    # 保存更改
    await old_translation.save()
    return {
        "success":True,
        "message":"Translation updated successfully"
    }



@translation_router.delete("/{translation_id}")
async def delete_translation(translation_id:str):
    delete_count = await TranslationRecord.filter(translation_id=translation_id).delete()
    if not delete_count:
        return{
            "success":False,
            "message":"Translation not found",
        }
    return {
        "success":True,
        "message":"Translation deleted successfully",
    }


# 模拟Supabase文件上传功能
@translation_router.post("/uploadAudio")
async def upload_audio_file(
    file: UploadFile = File(...),
    fileName: str = Form(...)
):
    """
    音频文件上传端点，模拟Supabase Storage功能
    
    前端调用示例：
    const formData = new FormData();
    formData.append('file', blob, fileName);
    formData.append('fileName', fileName);
    
    fetch('/uploadAudio', {
        method: 'POST',
        body: formData
    })
    """
    try:
        # 验证文件类型
        allowed_extensions = {'.wav', '.mp3', '.ogg', '.webm', '.m4a'}
        file_extension = Path(fileName).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file_extension}. 支持的格式: {', '.join(allowed_extensions)}"
            )
        
        # 生成唯一文件名，避免冲突
        unique_filename = f"{fileName}"
        file_path = UPLOAD_DIRECTORY / unique_filename
        
        # 异步保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # 生成公开访问URL（类似Supabase的publicUrl）
        public_url = f"/audio/{unique_filename}"
        
        return {
            "success": True,
            "message": "文件上传成功",
            "publicUrl": public_url,
            "fileName": unique_filename,
            "originalName": fileName,
            "fileSize": len(content),
            "uploadTime": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


# 音频文件访问端点
@translation_router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    提供音频文件的公开访问，类似Supabase Storage的公开URL
    """
    file_path = UPLOAD_DIRECTORY / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件未找到或过期销毁")
    
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename
    )
