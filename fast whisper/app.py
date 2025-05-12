from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import tempfile
from faster_whisper import WhisperModel
import time
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import pathlib
import logging
import re
import asyncio
import numpy as np
import wave
import io
import base64
import json

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 获取当前文件的目录
current_dir = pathlib.Path(__file__).parent.absolute()

# 创建FastAPI应用实例
app = FastAPI(
    title="Fast Whisper实时转录API",
    description="使用Fast Whisper进行实时语音转录的API",
    version="0.1.0"
)

# 挂载静态文件目录
static_dir = os.path.join(current_dir, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_text(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

# 定义数据模型
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float
    is_available: bool = True

class TranscriptionResult(BaseModel):
    text: str
    segments: List[Dict[str, Any]]
    language: str
    processing_time: float

# 服务端VAD配置
class ServerVADConfig:
    # 定义默认VAD参数
    def __init__(self):
        # VAD相关参数
        self.vad_filter = True                # 是否启用VAD过滤
        self.vad_threshold = 0.5              # VAD阈值(0-1之间，越高越严格)
        self.min_speech_duration_ms = 250     # 最小语音持续时间(毫秒)
        self.min_silence_duration_ms = 2000   # 最小静默持续时间(毫秒)
        self.window_size_samples = 1024       # VAD窗口大小
        self.speech_pad_ms = 300              # 语音片段前后填充时间(毫秒)

# 创建全局VAD配置实例
vad_config = ServerVADConfig()

# 初始化Whisper模型
# 这里使用"tiny"模型以便快速加载，实际使用时可以选择更大的模型如"base"、"small"、"medium"、"large"
model_size = "tiny"
# 使用CPU模式，如果有GPU可以设置device="cuda"
whisper_model = None

# 延迟加载模型
def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
    return whisper_model

# 模拟数据库
items_db = []
item_id_counter = 1

# WebSocket路由
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.info("WebSocket连接已建立")
    
    try:
        # 获取Whisper模型
        model = get_whisper_model()
        
        # 音频处理参数
        sample_rate = 16000  # Whisper模型需要16kHz
        audio_buffer = []  # 存储接收到的音频数据
        processed_duration = 0  # 已处理的音频时长（毫秒）
        last_processed_length = 0  # 上次处理的音频长度
        
        while True:
            # 接收WebSocket数据
            data = await websocket.receive_text()
            
            # 检查是否是控制命令
            if data == "START_RECORDING":
                logger.info("开始录音")
                audio_buffer = []  # 清空缓冲区
                processed_duration = 0  # 重置已处理时长
                last_processed_length = 0  # 重置上次处理长度
                await manager.send_text("录音已开始", websocket)
                continue
                
            if data == "STOP_RECORDING":
                logger.info("停止录音")
                # 处理完整的音频
                if audio_buffer:
                    try:
                        # 处理所有累积的音频数据
                        result = await process_audio_buffer(audio_buffer, model)
                        await manager.send_text(f"FINAL_RESULT:{result}", websocket)
                    except Exception as e:
                        logger.error(f"处理完整音频时出错: {str(e)}")
                        await manager.send_text(f"ERROR:处理音频失败 - {str(e)}", websocket)
                
                audio_buffer = []  # 重置缓冲区
                processed_duration = 0  # 重置已处理时长
                last_processed_length = 0  # 重置上次处理长度
                continue
            
            # 检查是否是VAD配置命令
            if data.startswith("CONFIG:VAD:"):
                try:
                    # 解析VAD配置
                    config_data = data[11:] # 去掉前缀"CONFIG:VAD:"
                    # 使用JSON解析
                    config_dict = json.loads(config_data)
                    
                    # 更新VAD配置
                    for key, value in config_dict.items():
                        if hasattr(vad_config, key):
                            setattr(vad_config, key, value)
                            logger.info(f"更新VAD配置 {key}={value}")
                    
                    await manager.send_text("VAD配置已更新", websocket)
                except Exception as e:
                    logger.error(f"更新VAD配置时出错: {str(e)}")
                    await manager.send_text(f"ERROR:更新VAD配置失败 - {str(e)}", websocket)
                continue
            
            # 处理音频数据
            try:
                # 解码Base64音频数据
                if data.startswith("DATA:"):
                    audio_data = data[5:]  # 去掉前缀"DATA:"
                    audio_bytes = base64.b64decode(audio_data)
                    audio_buffer.append(audio_bytes)
                    
                    # 当累积了足够的音频数据时进行实时转录
                    if len(audio_buffer) >= 5:  # 大约2-3秒的音频
                        # 计算当前缓冲区总长度
                        current_buffer_length = len(audio_buffer)
                        
                        # 如果有新数据，则进行增量处理
                        if current_buffer_length > last_processed_length:
                            # 只处理新增部分
                            partial_buffer = audio_buffer.copy()  # 创建缓冲区副本进行处理
                            
                            # 异步处理音频，不阻塞WebSocket连接
                            asyncio.create_task(
                                process_and_send_incremental_result(
                                    partial_buffer, 
                                    model, 
                                    websocket, 
                                    last_processed_length, 
                                    processed_duration
                                )
                            )
                            
                            # 更新已处理长度
                            last_processed_length = current_buffer_length
            
            except Exception as e:
                logger.error(f"处理音频数据时出错: {str(e)}")
                await manager.send_text(f"ERROR:处理音频数据失败 - {str(e)}", websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket连接已关闭")
    except Exception as e:
        logger.exception(f"WebSocket处理过程中出错: {str(e)}")
        try:
            await manager.send_text(f"ERROR:服务器错误 - {str(e)}", websocket)
        except:
            pass
        manager.disconnect(websocket)

# 新增：增量处理音频并返回结果
async def process_and_send_incremental_result(audio_buffer, model, websocket, prev_processed_length, processed_duration):
    try:
        # 处理整个音频缓冲区
        full_result = await process_audio_buffer(audio_buffer, model)
        
        # 向客户端发送增量结果
        await manager.send_text(f"INCREMENTAL_RESULT:{full_result}:{processed_duration}", websocket)
        
        # 同时发送部分结果保持兼容性
        await manager.send_text(f"PARTIAL_RESULT:{full_result}", websocket)
        
        # 更新已处理的音频时间
        # 假设每块音频约500ms，这个值应该更精确地计算
        return processed_duration + ((len(audio_buffer) - prev_processed_length) * 500)
    except Exception as e:
        logger.error(f"处理增量音频时出错: {str(e)}")
        await manager.send_text(f"ERROR:处理音频失败 - {str(e)}", websocket)
        return processed_duration

# 保留原有函数以保持兼容性
async def process_and_send_result(audio_buffer, model, websocket):
    try:
        result = await process_audio_buffer(audio_buffer, model)
        await manager.send_text(f"PARTIAL_RESULT:{result}", websocket)
    except Exception as e:
        logger.error(f"处理音频时出错: {str(e)}")
        await manager.send_text(f"ERROR:处理音频失败 - {str(e)}", websocket)

async def process_audio_buffer(audio_buffer, model):
    """处理音频缓冲区并返回转录结果"""
    try:
        # 合并所有音频数据
        combined_audio = b''.join(audio_buffer)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(combined_audio)
            temp_audio_path = temp_audio.name
        
        try:
            # 使用Whisper模型转录，添加VAD配置
            logger.info(f"开始转录音频: {temp_audio_path}, VAD配置: vad_filter={vad_config.vad_filter}, threshold={vad_config.vad_threshold}")
            
            # 应用VAD过滤
            segments, info = model.transcribe(
                temp_audio_path, 
                beam_size=5,
                vad_filter=vad_config.vad_filter,
                vad_parameters={
                    "threshold": vad_config.vad_threshold,
                    "min_speech_duration_ms": vad_config.min_speech_duration_ms,
                    "min_silence_duration_ms": vad_config.min_silence_duration_ms,
                    "window_size_samples": vad_config.window_size_samples,
                    "speech_pad_ms": vad_config.speech_pad_ms
                }
            )
            
            # 提取文本
            transcription_text = ""
            for segment in segments:
                transcription_text += segment.text + " "
            
            logger.info(f"转录完成: '{transcription_text.strip()}'")
            return transcription_text.strip()
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
                logger.info(f"已删除临时文件: {temp_audio_path}")
    
    except Exception as e:
        logger.exception(f"处理音频缓冲区时出错: {str(e)}")
        raise

# 路由定义
@app.get("/", response_class=HTMLResponse)
async def root():
    # 返回前端页面
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/items", response_model=List[Item])
async def read_items():
    return items_db

@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="找不到该商品")

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    global item_id_counter
    new_item = item.model_copy()
    new_item.id = item_id_counter
    item_id_counter += 1
    items_db.append(new_item)
    return new_item

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item):
    for i, stored_item in enumerate(items_db):
        if stored_item.id == item_id:
            update_item = item.model_copy()
            update_item.id = item_id
            items_db[i] = update_item
            return update_item
    raise HTTPException(status_code=404, detail="找不到该商品")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            del items_db[i]
            return {"message": f"已删除ID为{item_id}的商品"}
    raise HTTPException(status_code=404, detail="找不到该商品")

@app.post("/transcribe", response_model=TranscriptionResult)
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    上传音频文件并使用Fast Whisper进行转录
    """
    try:
        logger.info(f"接收到文件: {audio_file.filename}, 内容类型: {audio_file.content_type}")
        
        # 检查文件是否存在
        if not audio_file or not audio_file.filename:
            logger.error("没有上传文件或文件名为空")
            raise HTTPException(status_code=400, detail="没有上传文件或文件名为空")
        
        # 检查文件格式
        valid_extensions = ('.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm')
        valid_content_types = (
            'audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/wave', 
            'audio/x-m4a', 'audio/m4a', 'audio/ogg', 'audio/flac',
            'audio/webm', 'video/webm'
        )
        
        filename_valid = False
        content_type_valid = False
        
        # 检查文件名扩展
        if audio_file.filename.lower().endswith(valid_extensions):
            filename_valid = True
        
        # 检查内容类型
        if audio_file.content_type in valid_content_types:
            content_type_valid = True
            
        # 如果文件名中没有扩展名但MIME类型有效，为文件添加扩展名
        if content_type_valid and not filename_valid:
            # 从content_type推断扩展名
            if 'webm' in audio_file.content_type:
                ext = '.webm'
            elif 'mp3' in audio_file.content_type or 'mpeg' in audio_file.content_type:
                ext = '.mp3'
            elif 'wav' in audio_file.content_type or 'wave' in audio_file.content_type:
                ext = '.wav'
            elif 'm4a' in audio_file.content_type:
                ext = '.m4a'
            elif 'ogg' in audio_file.content_type:
                ext = '.ogg'
            elif 'flac' in audio_file.content_type:
                ext = '.flac'
            else:
                ext = '.audio'  # 默认扩展名
                
            audio_file.filename = f"recording{ext}"
            filename_valid = True
            logger.info(f"从内容类型推断文件名: {audio_file.filename}")
        
        if not (filename_valid or content_type_valid):
            logger.error(f"不支持的文件格式: {audio_file.filename}, 内容类型: {audio_file.content_type}")
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的音频格式。支持的格式: MP3, WAV, M4A, OGG, FLAC, WEBM。"
                       f"当前文件: {audio_file.filename}, 内容类型: {audio_file.content_type}"
            )
        
        start_time = time.time()
        
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_audio:
            logger.info(f"保存临时文件: {temp_audio.name}")
            content = await audio_file.read()
            logger.info(f"文件大小: {len(content)} 字节")
            temp_audio.write(content)
            temp_audio_path = temp_audio.name
        
        # 检查临时文件是否创建成功
        if not os.path.exists(temp_audio_path) or os.path.getsize(temp_audio_path) == 0:
            logger.error(f"临时文件创建失败或为空: {temp_audio_path}")
            raise HTTPException(status_code=500, detail="文件处理失败")
        
        logger.info("开始转录音频...")
        # 获取模型并进行转录
        model = get_whisper_model()
        segments, info = model.transcribe(temp_audio_path, beam_size=5)
        
        # 处理转录结果
        transcription_text = ""
        segments_data = []
        
        for segment in segments:
            transcription_text += segment.text + " "
            segments_data.append({
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "words": [{"word": word.word, "start": word.start, "end": word.end, "probability": word.probability} for word in (segment.words or [])]
            })
        
        processing_time = time.time() - start_time
        logger.info(f"转录完成，耗时: {processing_time:.2f}秒，检测语言: {info.language}")
        
        return {
            "text": transcription_text.strip(),
            "segments": segments_data,
            "language": info.language,
            "processing_time": processing_time
        }
    
    except Exception as e:
        logger.exception(f"转录过程中出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"转录过程中出错: {str(e)}")
    
    finally:
        # 删除临时文件
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            logger.info(f"已删除临时文件: {temp_audio_path}")

# 如果直接运行此文件，启动服务器
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)