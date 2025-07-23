import asyncio
from locale import normalize
import re
import httpx
import uuid
from typing import Dict,List,Optional,Any,Union
import tempfile
import os

from config.settings import Settings
from utils.exceptions import TTSException
from utils.language_utils import normalize_language_code
from utils.audio_utils import audio_converter, mp3_to_pcm, pcm_to_adpcm

class TTSService:
    """文本转语音服务"""

    def __init__(self):
        self.api_key = Settings.OPENAI_API_KEY
        self.model = "tts-1"
        self.api_url = "https://api.openai.com/v1/audio/speech"
        self.timeout = 30.0

        # TTS 任务管理
        self.active_tasks: Dict[str,asyncio.Task] = {} # 任务ID -> 任务
        self.task_status: Dict[str,str] = {} # "playing","paused","completed"

        # 语言配置
        self.voice_mapping = {
            "zh-CN": "alloy",    # 中文使用 alloy
            "en-US": "shimmer",  # 英文使用 shimmer
            "ja-JP": "nova",     # 日文使用 nova
            "ko-KR": "echo",     # 韩文使用 echo
            "fr-FR": "fable",    # 法文使用 fable
            "de-DE": "onyx",     # 德文使用 onyx
            "es-ES": "alloy",    # 西班牙文使用 alloy
            "it-IT": "shimmer",  # 意大利文使用 shimmer
            "ru-RU": "echo",     # 俄文使用 echo
            "pt-PT": "nova",     # 葡萄牙文使用 nova
            "ar-SA": "onyx",     # 阿拉伯文使用 onyx
            "vi-VN": "fable",    # 越南文使用 fable
            "tl-PH": "nova"      # 菲律宾文使用 nova
        }

        self.default_voice = "alloy"

    async def synthesize(self,text:str,language:str,output_format:str="mp3") ->Dict[str,Any]:
        """
        文本转语音
        
        Args:
            text: 要转换的文本
            language: 语言代码
            output_format: 输出格式 ("mp3", "wav", "pcm", "adpcm")
            
        Returns:
            包含音频数据的字典：
            {
                "task_id": "任务ID",
                "audio_data": "音频数据",
                "format": "音频格式",
                "language": "语言代码",
                "text": "原文本"
            }
        """
        try:
            # 生成任务ID
            task_id = f"tts_{uuid.uuid4().hex[:8]}"

            # 标准化语言代码
            normalize_lang = normalize_language_code(language)

            # 选择合适的声音
            voice = self.voice_mapping.get(normalize_lang,self.default_voice)

            # 调用OpenAI TTS API
            mp3_data = await self._call_tts_api(text,voice)

            # 根据需要的格式转换音频
            audio_data = await self._convert_to_format(mp3_data,output_format)

            return {
                "task_id": task_id,
                "audio_data": audio_data,
                "format": output_format,
                "language": language,
                "text": text,
                "voice": voice
            }
        except Exception as e:
            raise TTSException(f"TTS合成失败: {str(e)}")
        
    async def synthesize_streaming(self,text:str,language:str,chunk_callback) ->str:
        """
        流式文本转语音（分块处理）
        
        Args:
            text: 要转换的文本
            language: 语言代码
            chunk_callback: 音频块回调函数
            
        Returns:
            任务ID
        """
        try:
            # 生成任务ID 
            task_id = f"tts_stream_{uuid.uuid4().hex[:8]}"

            # 创建异步任务
            task = asyncio.create_task(
                self._streaming_synthesis(task_id,text,language,chunk_callback)
            )

            self.active_tasks[task_id] = task
            self.task_status[task_id] = "playing"

            return task_id
        
        except Exception as e:
            raise TTSException(f"流式TTS合成失败: {str(e)}")

    async def _streaming_synthesis(self,task_id:str,text:str,language:str,chunk_callback):
        """
        执行流式合成
        """
        try:
            # 标准化语言代码
            normalize_lang = normalize_language_code(language)

            # 选择合适的声音
            voice = self.voice_mapping.get(normalize_lang,self.default_voice)

            # 调用 TTS API 获取MP3数据
            mp3_data = await self._call_tts_api(text,voice)

            # 转换为PCM
            pcm_data = mp3_to_pcm(mp3_data,target_sample_rate=16000)

            # 转化为ADPCM分块
            adpcm_chunks = pcm_to_adpcm(pcm_data,chunk_size=256)

            # 流式发送音频块
            for i,chunk in enumerate(adpcm_chunks):
                # 检查任务是否被停止
                if self.task_status.get(task_id) == "stopped":
                    print(f"流式TTS任务已停止: {task_id}")
                    break

                # 发送音频块
                await chunk_callback({
                    "task_id": task_id,
                    "chunk_index":i,
                    "chunk_data":chunk,
                    "is_final":i == len(adpcm_chunks) - 1,
                    "format":"adpcm",
                    "text":text,
                })

                # 等待100ms, 控制流式速度
                await asyncio.sleep(0.2)

            # 任务完成
            self.task_status[task_id] = "completed"
            print(f"流式TTS任务完成: {task_id}")

        except Exception as e:
            self.task_status[task_id] = "error"
            raise TTSException(f"流式TTS合成失败: {str(e)}")
        finally:
            # 清理任务
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    async def stop_tts(self,task_id:str) ->bool:
        """
        停止TTS播放
        
        Args:
            task_id: 要停止的任务ID
            
        Returns:
            是否成功停止
        """
        try: 
            if task_id in self.active_tasks:
                # 标记任务为停止
                self.task_status[task_id] = "stopped"

                # 取消任务
                task = self.active_tasks[task_id]
                task.cancel()
            
                # 等待任务结束
                try:
                    await task
                except asyncio.CancelledError:
                    pass

                # 清理任务
                del self.active_tasks[task_id]
                print(f"TTS任务已停止: {task_id}")
                return True
            
            else:
                print(f"TTS任务不存在: {task_id}")
                return False
        
        except Exception as e:
            print(f"停止TTS任务失败: {str(e)}")
            return False
    
    def stop_all_tts(self) -> int:
        """
        停止所有TTS任务
        
        Returns:
            停止的任务数量
        """
        stopped_count = 0
        task_ids = list(self.active_tasks.keys())

        for task_id in task_ids:
            try:
                asyncio.create_task(self.stop_tts(task_id))
                stopped_count += 1
            except Exception as e:
                print(f"停止TTS任务失败: {task_id} - {str(e)}")

        return stopped_count

    async def _call_tts_api(self,text:str,voice:str) -> bytes:
        """
        调用 OpenAI TTS API
        
        Args:
            text: 要转换的文本
            voice: 声音类型
            
        Returns:
            MP3 音频数据
        """
        try: 
            # 准备api请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 准备请求数据
            data = {
                "model": self.model,
                "input": text,
                "voice": voice,
            }

            # 发送 API 请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=data
                )

            # 检查响应
            if response.status_code !=200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_detail = error_json["error"].get("message",error_json["error"])
                except:
                    pass
                
                raise TTSException(f"API request failed with status {response.status_code}: {error_detail}")
            
            # 返回音频数据
            return response.content
        
        except httpx.TimeoutException:
            raise TTSException(f"API request timed out after {self.timeout} seconds")
        except Exception as e:
            if isinstance(e,TTSException):
                raise e
            else:
                raise TTSException(f"API request failed: {str(e)}")

    async def _convert_to_format(self,mp3_data:bytes,target_format:str) -> Union[bytes,List[bytes]]:
        """
        转换音频格式
        
        Args:
            mp3_data: MP3 音频数据
            target_format: 目标格式
            
        Returns:
            转换后的音频数据
        """
        try: 
            if target_format.lower() == "mp3":
                return mp3_data

            pcm_data = mp3_to_pcm(mp3_data,target_sample_rate=16000)

            if target_format.lower() == "pcm":
                return pcm_data.tobytes()
            elif target_format.lower() == "wav":
                return audio_converter.pcm_to_wav(pcm_data,sample_rate=16000)
            elif target_format.lower() == "adpcm":
                return audio_converter.pcm_to_adpcm(pcm_data,chunk_size=256)
            else:
                raise TTSException(f"不支持的音频格式: {target_format}")
        
        except Exception as e:
            raise TTSException(f"音频格式转换失败: {str(e)}")

    def get_task_status(self,task_id:str)->Optional[str]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态
        """
        return self.task_status.get(task_id)

    def get_active_tasks(self) -> List[str]:
        """
        获取所有活动任务ID
        
        Returns:
            活动任务ID列表
        """
        return list(self.active_tasks.keys())

    def get_supported_voices(self) -> Dict[str,str]:
        """
        获取支持的声音映射
        
        Returns:
            语言到声音的映射
        """
        return self.voice_mapping.copy()

# 创建全局实例
tts_service = TTSService()