import asyncio
import json 
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import webbrowser
from fastapi import WebSocket
from numpy.random import normal
import os
import re

from utils.exceptions import TranslationException,TTSException,IntentRecognitionException
from services.summary_service import summary_service    
from services.asr_service import asr_service
from services.translation_service import translation_service
from services.tts_service import tts_service
from services.intent_recognition_service import intent_recognition_service
from services.title_service import title_service
from utils.sessions import Session


logging.basicConfig(level=logging.INFO)


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        """初始化WebSocket连接管理器"""
        self.active_connections: Dict[str,WebSocket] = {} # session_id: connection
        self.sessions: Dict[str,Session] = {} # session_id: session
        self.heartbeat_task: Dict[str,asyncio.Task] = {} # session_id: heartbeat_task
        self.heartbeat_interval = 30 # 心跳间隔
        self.tts_task: Dict[str,asyncio.Task] = {} # session_id: tts_task

        self.audio_buffers:Dict[str,List[bytes]] = {} # session_id: audio_buffers
        self.base64_buffers:Dict[str,Dict[str,str]] = {} # session_id: {chunk_id: base64_data}

        self.supported_languages = [
            "zh-CN", 
            "en-US", 
            "ja-JP", 
            "ko-KR", 
            "fr-FR", 
            "de-DE", 
            "es-ES", 
            "it-IT", 
            "ru-RU", 
            "pt-PT",
            "ar-SA"
            ]

        # 系统状态
        self.system_status ={
            "asr_status": "online",
            "translation_status": "online",
            "tts_status":"online",
            "queue_length":0,
        }

    async def connect(self,websocket:WebSocket,session_id:Optional[str]=None):
        """
        处理WebSocket连接

        Args:
            websocket: WebSocket 连接对象
            session_id: 会话ID，如果为None，则创建新会话

        Returns:
            session_id: 会话ID
        """
        try:
            # 接受WebSocket连接
            await websocket.accept()

            if not session_id:
                session_id = f"session_{uuid.uuid4().hex[:8]}"

            # 创建会话
            session = Session(session_id)

            # 保存连接和会话
            self.active_connections[session_id] = websocket
            self.sessions[session_id] = session

            # 发送连接确认消息
            await self._send_message(session_id,{
                "type":"connected",
                "data":{
                    "session_id":session_id,
                    "server_time":datetime.now().isoformat(),
                    "supported_languages":self.supported_languages,
                }
            })

            # 启动心跳检测
            self.heartbeat_task[session_id] = asyncio.create_task(
                self._heartbeat_task(session_id)
            )

            logging.info(f"WebSocket连接成功，会话ID: {session_id}")
            return session_id

        except Exception as e:
            logging.error(f"WebSocket连接失败: {e}")
            return None

    async def disconnect(self,session_id:str):
        """
        处理WebSocket断开连接

        Args:
            session_id: 会话ID
        """
        try:
            # 停止当前会话的所有TTS
            if session_id in self.sessions:
                tts_service.stop_all_tts()

                # 保存会话历史
                await self._save_session_history(session_id)

                # 生成标题和分类
                await title_service.generate_title(session_id)

            # 清理连接和会话
            if session_id in self.active_connections:
                del self.active_connections[session_id]
            
            # 取消心跳检测
            if session_id in self.heartbeat_task:
                self.heartbeat_task[session_id].cancel()
                del self.heartbeat_task[session_id]

            # 清理会话
            if session_id in self.sessions:
                del self.sessions[session_id]

            # 清理TTS任务
            if session_id in self.tts_task:
                self.tts_task[session_id].cancel()
                del self.tts_task[session_id]

            logging.info(f"WebSocket断开连接，会话ID: {session_id}")

        except Exception as e:
            logging.error(f"WebSocket断开连接失败: {e}")

    async def _save_session_history(self,session_id:str):
        """
        保存会话历史
        """
        try:
            # 导入History模型
            from models.history import History

            # 获取会话
            session = self.sessions.get(session_id)
            if not session:
                await self._send_error_message(session_id,"SESSION_NOT_FOUND")
                return

            if not session.conversation or len(session.conversation) == 0:
                logging.warning(f"会话ID {session_id} 没有对话历史")
                return

            # 转换格式
            conversation_data = []
            for i,conv in enumerate(session.conversation):
                conversation_data.append({
                    "id":f"record_{i+1:03d}",
                    "source_text":conv["source_text"],
                    "source_language":conv["source_language"],
                    "target_text":conv["target_text"],
                    "target_language":conv["target_language"],
                    "timestamp":conv.get("timestamp",datetime.now().isoformat())
                })
            
            # 检查是否存在历史记录
            existing_history = await History.get_by_session_id(session_id)

            if existing_history:
                # 更新历史记录
                existing_history.conversation= conversation_data
                existing_history.end_time = datetime.now()
                await existing_history.save()
                logging.info(f"更新会话历史记录: {session_id}")
            else:
                # 创建新历史记录
                await History.create_history(session_id,conversation_data)
                logging.info(f"创建会话历史记录: {session_id}")

        except Exception as e:
            logging.error(f"保存会话历史记录失败: {e}")
            await self._send_error_message(session_id,f"SAVE_SESSION_HISTORY_ERROR: {e}")


    async def handle_message(self,session_id:str,message:dict):
        """
        处理WebSocket消息
        
        Args:
            session_id: 会话ID
            message: 接收到的消息
        """
        try:
            message_type = message.get("type")
            data = message.get("data",{})

            if message_type == "audio_stream":
                await self._handle_audio_stream(session_id,data)
            elif message_type == "stop_tts":
                await self._handle_stop_tts(session_id,data)
            elif message_type == "change_target_language":
                await self._handle_change_target_language(session_id,data)
            elif message_type == "ping":
                await self._handle_ping(session_id,data)
            elif message_type =="get_system_status":
                await self._handle_get_system_status(session_id)
            elif message_type == "generate_summary":
                await self._handle_generate_summary(session_id,data)
            else:
                await self._send_error_message(session_id,"INVALID_MESSAGE_TYPE")

        except Exception as e:
            logging.error(f"处理消息失败: {e}")
            await self._send_error_message(session_id,f"MESSAGE_HANDLING_ERROR: {e}")

    async def _handle_audio_stream(self,session_id:str,data:dict):
        """
        处理音频流

        Args:
            session_id: 会话ID
            data: 接收到的消息
        """
        try:
            # 获取会话
            session = self.sessions.get(session_id)
            if not session:
                await self._send_error_message(session_id,"SESSION_NOT_FOUND")
                return

            # 停止当前会话的TTS
            # await self._handle_stop_tts(session_id,{"audio_id":None})
            if session_id in self.tts_task:
                self.tts_task[session_id].cancel()
                del self.tts_task[session_id]

            # 获取音频流 先保存到音频缓冲区，等到is_final为True时，再进行ASR转写
            audio_chunk = data.get("audio_chunk")
            audio_format = str(data.get("format"))
            chunk_id = data.get("chunk_id")  # 获取chunk_id

            
            # 如果音频缓冲区不存在，则创建
            if session_id not in self.audio_buffers:
                self.audio_buffers[session_id] = []
            if session_id not in self.base64_buffers:
                self.base64_buffers[session_id] = {}  # 改为字典存储 {chunk_id: base64_data}

            # 转换音频数据
            if audio_chunk:
                if isinstance(audio_chunk,str):
                    # 保存到base64缓冲区，使用chunk_id作为键
                    if chunk_id:
                        self.base64_buffers[session_id][chunk_id] = audio_chunk
                    else:
                        # 如果没有chunk_id，使用时间戳作为键
                        fallback_key = f"chunk_{len(self.base64_buffers[session_id])}"
                        self.base64_buffers[session_id][fallback_key] = audio_chunk
                elif isinstance(audio_chunk,list):
                    # 将list转换为bytes
                    import numpy as np
                    pcm_array = np.array(audio_chunk, dtype=np.uint8)
                    audio_chunk = pcm_array.tobytes()
                    self.audio_buffers[session_id].append(audio_chunk)
                elif isinstance(audio_chunk,bytes):
                    self.audio_buffers[session_id].append(audio_chunk)
                else:
                    logging.warning(f"音频数据格式错误: {type(audio_chunk)}")
                    return

            # 只有当is_final为True时，才进行ASR转写
            if not data.get("is_final"):
                # 如果不是最后一个音频块，直接返回
                return
                
            # 将音频缓冲区中的音频数据合并
            audio_data = b''.join(self.audio_buffers[session_id])
            
            # 按chunk_id顺序排序后拼接base64数据
            base64_chunks = self.base64_buffers[session_id]
            if base64_chunks:
                # 提取chunk_id中的数字部分进行排序
                def extract_chunk_number(chunk_id: str) -> int:
                    try:
                        # 从 "chunk_0", "chunk_1", "chunk_19" 等格式中提取数字
                        if chunk_id.startswith("chunk_"):
                            return int(chunk_id.split("_")[1])
                        else:
                            # 如果不是标准格式，返回一个大数以便排在最后
                            return 999999
                    except (ValueError, IndexError):
                        return 999999
                
                # 按chunk_id中的数字顺序排序
                sorted_chunk_ids = sorted(base64_chunks.keys(), key=extract_chunk_number)
                base64_data = ''.join([base64_chunks[chunk_id] for chunk_id in sorted_chunk_ids])

                # 移除base64数据中的换行符和空白字符
                base64_data = base64_data.replace('\n', '').replace(' ', '').replace('\r', '')
                
                print(f"🔗 按顺序拼接base64数据: {len(sorted_chunk_ids)} 个块")
                print(f"🔗 总长度: {len(base64_data)} 字符")
            else:
                base64_data = ""


            # 也可以直接拼接base64数据
            # base64_data = ""
            # base64_data = ''.join(self.base64_buffers[session_id].values())
            print(f"音频数据长度: {len(base64_data)} ")
            
            # 清空音频缓冲区
            self.audio_buffers[session_id] = []
            self.base64_buffers[session_id] = {}

            # 1. ASR 转写
            try:
                if len(base64_data) > 0:
                    transcript_result = await asr_service.transcribe(base64_data,format=audio_format)

                    text = transcript_result["text"]
                    detected_lang = transcript_result["language"]
                    target_lang = ""

                    # 1.1 意图识别
                    try:
                        intent_result = await intent_recognition_service.analyze_intent(session,text)
                        print(f"意图识别结果: {intent_result}")

                        # 1.2 根据意图决定是否更新翻译内容
                        if intent_result.get("intent") == "translate":
                            text = intent_result.get("source_text",text)
                            target_lang = intent_result.get("target_language","")
                            # 如果意图识别结果的target_language与detected_lang相同，则从会话中获取target_language
                            if target_lang == detected_lang:
                                target_lang = ""
                        else:
                            target_lang = ""
                            
                    except IntentRecognitionException as e:
                        logging.error(f"意图识别失败: {e}")
                        await self._send_error_message(session_id,f"INTENT_RECOGNITION_ERROR: {e}")
                        return
                else:
                    logging.warning(f"音频缓冲区为空，跳过ASR转写")
                    return
                
                await self._send_message(session_id,{
                    "type": "transcript_result",
                    "data":{
                        "text":text,
                        "language":detected_lang,
                        "confidence":transcript_result["confidence"],
                        "is_final":transcript_result["is_final"],
                        "timestamp":datetime.now().isoformat(),
                    }
                })

            except Exception as e:
                logging.error(f"ASR转写失败: {e}")
                await self._send_error_message(session_id,f"ASR_ERROR: {e}")
                return
            
            # 2. 翻译
            
            if text.strip():
                try:
                    translation_result = await translation_service.translate_and_save(session, text, detected_lang,target_lang)
                    # 发送翻译结果
                    await self._send_message(session_id,{
                        "type":"translation_result",
                        "data":{
                            "source_text": translation_result["source_text"],
                            "target_text": translation_result["target_text"],
                            "source_language": translation_result["source_language"],
                            "target_language": translation_result["target_language"],
                            "confidence": translation_result.get("confidence",0.98),
                        }
                    })
                
                    # 3. TTS
                    translated_text=translation_result["target_text"]
                    target_lang = translation_result["target_language"]

                    if translated_text.strip():
                        await self._handle_tts_synthesis(session_id,translated_text,target_lang)
                
                except TranslationException as e:
                    logging.error(f"翻译失败: {e}")
                    await self._send_error_message(session_id,f"TRANSLATION_ERROR: {e}")
                    return
        
        except Exception as e:
            logging.error(f"处理音频流失败: {e}")
            await self._send_error_message(session_id,f"AUDIO_PROCESSING_ERROR: {e}")
            return

    async def _handle_tts_synthesis(self,session_id:str,text:str,language:str):
        """
        处理TTS合成

        Args:
            session_id: 会话ID
            text: 要合成的文本
            language: 语言
        """
        try:
            # 流式合成TTS
            result = await tts_service.synthesize(text,language,output_format="mp3")
 
            await self._handle_tts_result(session_id,result)

            # 保存TTS任务
            self.tts_task[session_id] = asyncio.create_task(self._handle_tts_result(session_id,result))

        except TTSException as e:
            logging.error(f"TTS合成失败: {e}")
            await self._send_error_message(session_id,f"TTS_ERROR: {e}")
            return

    async def _handle_tts_result(self,session_id:str,result:dict):
        """
        处理TTS合成结果
        """
        try:
            websocket = self.active_connections.get(session_id)
            if websocket:
                await websocket.send_bytes(result["audio_data"])
        except Exception as e:
            logging.error(f"处理TTS合成结果失败: {e}")
            await self._send_error_message(session_id,f"TTS_RESULT_PROCESSING_ERROR: {e}")
            return

    async def _handle_stop_tts(self,session_id:str,data:dict):
        """
        处理停止TTS

        Args:
            session_id: 会话ID
            data: 接收到的消息
        """
        try:
            audio_id = data.get("audio_id")

            if audio_id:
                # 停止特定TTS
                success = await tts_service.stop_tts(audio_id)
                if success:
                    await self._send_message(session_id,{
                        "type":"tts-stopped",
                        "data":{
                            "audio_id":audio_id,
                            "stopped_at":datetime.now().isoformat()
                        }
                    })
            # TODO: 是否需要停止所有TTS？
            else:
                # 停止所有TTS
                stopped_count = tts_service.stop_all_tts()
                if stopped_count > 0:
                    await self._send_message(session_id,{
                        "type":"tts-stopped",
                        "data":{
                            "stopped_count":stopped_count,
                            "stopped_at":datetime.now().isoformat()
                        }
                    })

        except Exception as e:
            await self._send_error_message(session_id,f"TTS_STOP_ERROR: {e}")

    async def _handle_change_target_language(self,session_id:str,data:dict):
        """
        处理目标语言变更

        Args:
            session_id: 会话ID
            data: 接收到的消息
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                await self._send_error_message(session_id,"SESSION_NOT_FOUND")
                return
            
            new_language = data.get("current_language")
            if not new_language:
                await self._send_error_message(session_id,"LANGUAGE_REQUIRED")
                return
            
            previous_language = session.target_lang
            
            # 直接设置目标语言
            session.target_lang = new_language
            # 同时更新检测语言和会话语言列表
            session.update_detected_lang(new_language)
            
            await self._send_message(session_id,{
                "type":"target_language_changed",
                "data":{
                    "previous_language":previous_language,
                    "current_language":session.target_lang,
                    "changed_by":"voice_command"
                }
            })

        except Exception as e:
            await self._send_error_message(session_id,f"TARGET_LANGUAGE_CHANGE_ERROR: {e}")

    async def _handle_ping(self,session_id:str,data:dict):
        """
        处理心跳ping消息

        Args:
            session_id: 会话ID
            data: 接收到的消息
        """
        await self._send_message(session_id,{
            "type":"pong",
            "data":{
                "timestamp":datetime.now().isoformat(),
                "server_load": "normal"
            }
        })

    async def _handle_get_system_status(self,session_id:str):
        """
        处理获取系统状态请求

        Args:
            session_id: 会话ID
            data: 接收到的消息
        """
        await self._send_message(session_id,{
            "type":"system_status",
            "data":{
                "asr_status":self.system_status["asr_status"],
                "translation_status":self.system_status["translation_status"],
                "tts_status":self.system_status["tts_status"],
                "queue_length":self.system_status["queue_length"],
            }
        })

    async def _handle_generate_summary(self,session_id:str,data:dict):
        """
        处理生成总结请求
        
        Args:
            session_id: 会话ID
            data: 请求数据
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                await self._send_error_message(session_id,"SESSION_NOT_FOUND")
                return

            # 生成并导出总结
            result = await summary_service.generate_and_export_summary(session_id)

            await self._send_message(session_id,{
                "type":"summary_generated",
                "data":{
                    "summary":result["summary"],
                    "file_info":result["file_info"],
                    "success":result["success"]
                }
            })

        except Exception as e:
            await self._send_error_message(session_id,f"SUMMARY_GENERATION_ERROR: {e}")

    async def _heartbeat_task(self,session_id:str):
        """
        心跳任务

        Args:
            session_id: 会话ID
        """
        try:
            while session_id in self.active_connections:
                await asyncio.sleep(self.heartbeat_interval)

                if session_id in self.active_connections:
                    await self._send_message(session_id,{
                        "type":"heartbeat",
                        "data":{
                            "timestamp":datetime.now().isoformat(),
                            "session_active":True
                        }
                    })

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"心跳任务失败: {e}")

    async def _send_message(self,session_id:str,message:dict):
        """
        发送消息到websocket

        Args:
            session_id: 会话ID
            message: 消息
        """
        if session_id in self.active_connections:
            try:
                websocket = self.active_connections[session_id]
                await websocket.send_json(message)
            
            except Exception as e:
                logging.error(f"发送消息失败: {e}")
                # 如果发送失败，尝试重新连接3次
                for _ in range(3):
                    try:
                        await self.connect(websocket,session_id)
                        break
                    except Exception as e:
                        logging.error(f"重新连接失败: {e}")
                        await asyncio.sleep(1)
                else:
                    logging.error(f"会话ID {session_id} 重新连接失败")
                    # 如果重连失败，删除连接
                    await self.disconnect(session_id)

        else:
            logging.warning(f"会话ID {session_id} 不存在")

    async def _send_error_message(self,session_id:str,error_message:str):
        """
        发送错误消息到websocket

        Args:
            session_id: 会话ID
            error_message: 错误消息
        """
        await self._send_message(session_id,{
            "type":"error",
            "data":{
                "error":error_message,
                "timestamp":datetime.now().isoformat()
            }
        })

    def get_active_sessions(self) -> List[str]:
        """
        获取当前活跃的会话ID列表

        Returns:
            List[str]: 活跃的会话ID列表
        """
        return list(self.active_connections.keys())

    def get_session_status(self,session_id:str) -> Optional[dict]:
        """
        获取会话状态

        Args:
            session_id: 会话ID

        Returns:
            Optional[dict]: 会话状态，如果会话不存在则返回None
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                "session_id":session_id,
                "target_language":session.target_lang,
                "detected_language":session.detected_lang,
                "session_langs":session.session_langs,
                "conversation_count": len(session.conversation),
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat()
            }
        return None

# 创建WebSocketManager实例
websocket_manager = WebSocketManager()