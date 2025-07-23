from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import asyncio
import websockets
import json
import os
import base64
import wave
import io
import httpx
from typing import Dict, Any
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VOX 实时翻译器")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/css", StaticFiles(directory="css"), name="css")

# 添加HTML文件的静态文件服务
from fastapi.responses import FileResponse

@app.get("/test-websocket.html")
async def get_test_websocket():
    return FileResponse("test-websocket.html")

@app.get("/test-ble.html")
async def get_test_ble():
    return FileResponse("test-ble.html")

@app.get("/test-frontend.html")
async def get_test_frontend():
    return FileResponse("test-frontend.html")

@app.get("/quick-test.html")
async def get_quick_test():
    return FileResponse("quick-test.html")

@app.get("/index.html")
async def get_index_html():
    return FileResponse("index.html")

# 语言映射
LANGUAGE_MAP = {
    "en": "English",
    "zh": "Chinese",
    "ja": "Japanese", 
    "ko": "Korean"
}

# TTS语音映射
VOICE_MAP = {
    "en": "alloy",      # 英语使用alloy
    "zh": "nova",       # 中文使用nova  
    "ja": "shimmer",    # 日语使用shimmer
    "ko": "echo"        # 韩语使用echo
}

class RealtimeTranslator:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "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")
        self.client_sessions: Dict[str, Dict] = {}
        
    async def create_ephemeral_token(self) -> Dict[str, Any]:
        """创建临时API密钥"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/realtime/sessions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o-realtime-preview-2024-12-17",
                        "voice": "alloy",
                        "instructions": "You are a helpful real-time translator. When you receive audio, first transcribe it, then translate the transcribed text to the target language specified by the user.",
                        "input_audio_transcription": {
                            "model": "whisper-1"
                        }
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                session_data = response.json()
                logger.info(f"Session response: {session_data}")
                return session_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"OpenAI API Error: {e.response.text}")
        except Exception as e:
            logger.error(f"Failed to create ephemeral token: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

    async def connect_to_openai(self, ephemeral_key: str, target_language: str = "en"):
        """连接到OpenAI Realtime API"""
        uri = f"wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
        headers = {
            "Authorization": f"Bearer {ephemeral_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        try:
            websocket = await websockets.connect(uri, extra_headers=headers)
            
            # 发送会话配置 - 仅使用文本模式避免音频格式问题
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text"],  # 只使用文本模式
                    "instructions": f"You are a real-time translator. When you receive text to translate, translate it to {LANGUAGE_MAP.get(target_language, 'English')}. Provide only the translation without any additional text or explanation.",
                    "voice": VOICE_MAP.get(target_language, "alloy"),
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500,
                        "create_response": False
                    }
                }
            }
            
            await websocket.send(json.dumps(session_config))
            return websocket
            
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI: {e}")
            raise

    async def handle_openai_message(self, websocket_client, message_data, session_id):
        """处理OpenAI返回的消息"""
        try:
            message_type = message_data.get("type")
            logger.info(f"Received OpenAI message: {message_type}")
            
            if message_type == "session.created":
                await websocket_client.send_text(json.dumps({
                    "type": "session_ready",
                    "data": {"message": "会话已建立"}
                }))
                
            elif message_type == "session.updated":
                logger.info("Session updated successfully")
                
            elif message_type == "input_audio_buffer.speech_started":
                await websocket_client.send_text(json.dumps({
                    "type": "speech_started",
                    "data": {"message": "检测到语音输入"}
                }))
                if session_id in self.client_sessions:
                    self.client_sessions[session_id]["is_translating"] = False
                
            elif message_type == "input_audio_buffer.speech_stopped":
                await websocket_client.send_text(json.dumps({
                    "type": "speech_stopped", 
                    "data": {"message": "语音输入结束"}
                }))
                
            elif message_type == "conversation.item.input_audio_transcription.completed":
                transcript = message_data.get("transcript", "")
                logger.info(f"Transcription completed: {transcript}")
                
                # 发送转录结果给客户端
                await websocket_client.send_text(json.dumps({
                    "type": "transcription",
                    "data": {
                        "text": transcript,
                        "timestamp": datetime.now().isoformat()
                    }
                }))
                
                # 自动请求翻译
                if session_id in self.client_sessions and transcript.strip():
                    session_info = self.client_sessions[session_id]
                    if not session_info.get("is_translating", False):
                        session_info["is_translating"] = True
                        await self.request_translation(
                            session_info["openai_ws"],
                            transcript,
                            session_info["target_language"]
                        )
                
            elif message_type == "response.content_part.added":
                part = message_data.get("part", {})
                if part.get("type") == "text":
                    await websocket_client.send_text(json.dumps({
                        "type": "translation_started",
                        "data": {"message": "开始翻译"}
                    }))
                
            elif message_type == "response.text.delta":
                text_delta = message_data.get("delta", "")
                await websocket_client.send_text(json.dumps({
                    "type": "translation_delta",
                    "data": {"text": text_delta}
                }))
                
            elif message_type == "response.text.done":
                text_content = message_data.get("text", "")
                await websocket_client.send_text(json.dumps({
                    "type": "translation_complete",
                    "data": {
                        "text": text_content,
                        "timestamp": datetime.now().isoformat()
                    }
                }))
                if session_id in self.client_sessions:
                    self.client_sessions[session_id]["is_translating"] = False
                    
            elif message_type == "response.audio_transcript.done":
                transcript = message_data.get("transcript", "")
                if transcript:
                    await websocket_client.send_text(json.dumps({
                        "type": "translation_complete",
                        "data": {
                            "text": transcript,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    if session_id in self.client_sessions:
                        self.client_sessions[session_id]["is_translating"] = False
                
            elif message_type == "response.done":
                if session_id in self.client_sessions:
                    self.client_sessions[session_id]["is_translating"] = False
                
            elif message_type == "error":
                error_message = message_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"OpenAI error: {error_message}")
                
                if "already has an active response" not in error_message:
                    await websocket_client.send_text(json.dumps({
                        "type": "error",
                        "data": {"message": error_message}
                    }))
                
                if session_id in self.client_sessions:
                    self.client_sessions[session_id]["is_translating"] = False
                
        except Exception as e:
            logger.error(f"Error handling OpenAI message: {e}")

    async def request_translation(self, openai_ws, text, target_language):
        """请求翻译指定文本"""
        try:
            translation_request = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"Please translate this text to {LANGUAGE_MAP.get(target_language, 'English')}: \"{text}\""
                        }
                    ]
                }
            }
            
            await openai_ws.send(json.dumps(translation_request))
            
            # 只创建文本响应
            await openai_ws.send(json.dumps({
                "type": "response.create",
                "response": {
                    "modalities": ["text"],
                    "instructions": f"Translate the given text to {LANGUAGE_MAP.get(target_language, 'English')}. Provide only the translation without any additional text or explanation."
                }
            }))
            
        except Exception as e:
            logger.error(f"Error requesting translation: {e}")

    async def generate_tts(self, text: str, target_language: str = "en") -> str:
        """使用OpenAI TTS API生成语音 - 返回MP3格式"""
        try:
            # 优化：检查文本是否为空
            if not text.strip():
                logger.warning("Empty text provided for TTS generation")
                return ""
                
            async with httpx.AsyncClient() as client:
                # 优化：设置更高的超时时间，确保大段文本也能处理
                response = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "tts-1",  # 使用标准模型，速度更快
                        "input": text,
                        "voice": VOICE_MAP.get(target_language, "alloy"),
                        "response_format": "mp3",  # 使用MP3格式，浏览器兼容性更好
                        "speed": 1.0  # 标准速度，确保清晰度
                    },
                    timeout=60.0  # 增加超时时间
                )
                response.raise_for_status()
                
                # 将音频数据编码为base64
                audio_data = response.content
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                logger.info(f"TTS generated successfully, size: {len(audio_data)} bytes")
                return audio_base64
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error in TTS generation: {e.response.status_code} - {e.response.text}")
            return ""
        except Exception as e:
            logger.error(f"Error generating TTS: {e}")
            return ""

translator = RealtimeTranslator()

@app.get("/")
async def get_index():
    """返回主页面"""
    return FileResponse("index.html")

@app.get("/session")
async def create_session():
    """创建OpenAI会话并返回临时密钥"""
    try:
        session_data = await translator.create_ephemeral_token()
        logger.info(f"Created session: {session_data}")
        return session_data
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点处理客户端连接"""
    await websocket.accept()
    
    openai_ws = None
    session_id = None
    openai_task = None
    
    try:
        init_message = await websocket.receive_text()
        init_data = json.loads(init_message)
        
        if init_data.get("type") == "init":
            ephemeral_key = init_data.get("ephemeral_key")
            target_language = init_data.get("target_language", "en")
            session_id = init_data.get("session_id")
            
            logger.info(f"Initializing session with key: {ephemeral_key[:20]}...")
            
            if not ephemeral_key:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "Missing ephemeral key"}
                }))
                return
            
            openai_ws = await translator.connect_to_openai(ephemeral_key, target_language)
            
            translator.client_sessions[session_id] = {
                "websocket": websocket,
                "openai_ws": openai_ws,
                "target_language": target_language,
                "is_translating": False
            }
            
            openai_task = asyncio.create_task(
                listen_openai_messages(openai_ws, websocket, session_id)
            )
            
            async for message in websocket.iter_text():
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    if message_type == "audio_data":
                        audio_data = data.get("audio")
                        if audio_data and openai_ws:
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": audio_data
                            }))
                            
                    elif message_type == "start_recording":
                        if openai_ws:
                            # 开始新的录音会话，清除音频缓冲区
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.clear"
                            }))
                            
                    elif message_type == "stop_recording":
                        if openai_ws:
                            # 停止录音，提交当前音频缓冲区进行处理
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.commit"
                            }))
                            
                    elif message_type == "request_tts":
                        # 处理TTS请求
                        text = data.get("text", "")
                        if text and session_id in translator.client_sessions:
                            target_language = translator.client_sessions[session_id]["target_language"]
                            audio_base64 = await translator.generate_tts(text, target_language)
                            if audio_base64:
                                await websocket.send_text(json.dumps({
                                    "type": "tts_audio",
                                    "data": {"audio": audio_base64}
                                }))
                            else:
                                await websocket.send_text(json.dumps({
                                    "type": "error",
                                    "data": {"message": "TTS生成失败"}
                                }))
                            
                    elif message_type == "change_language":
                        target_language = data.get("target_language", "en")
                        if session_id in translator.client_sessions:
                            translator.client_sessions[session_id]["target_language"] = target_language
                            await openai_ws.send(json.dumps({
                                "type": "session.update",
                                "session": {
                                    "instructions": f"You are a real-time translator. When you receive text to translate, translate it to {LANGUAGE_MAP.get(target_language, 'English')}. Provide only the translation without any additional text or explanation."
                                }
                            }))
                            
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received from client")
                except Exception as e:
                    logger.error(f"Error processing client message: {e}")
                    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {"message": f"Connection error: {str(e)}"}
        }))
    finally:
        if openai_task:
            openai_task.cancel()
        if openai_ws:
            await openai_ws.close()
        if session_id and session_id in translator.client_sessions:
            del translator.client_sessions[session_id]

async def listen_openai_messages(openai_ws, client_ws, session_id):
    """监听OpenAI WebSocket消息"""
    try:
        async for message in openai_ws:
            try:
                data = json.loads(message)
                await translator.handle_openai_message(client_ws, data, session_id)
            except json.JSONDecodeError:
                logger.error("Invalid JSON from OpenAI")
            except Exception as e:
                logger.error(f"Error processing OpenAI message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("OpenAI WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error in OpenAI message listener: {e}")

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)