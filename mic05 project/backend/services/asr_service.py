from typing import Dict,Any,Union,List
import os
import numpy as np
from dotenv import load_dotenv
import tempfile
import httpx

from config.settings import Settings
from utils.language_utils import detect_language, normalize_language_code
from utils.exceptions import ASRException
from utils.audio_utils import AudioConverter, process_audio_to_wav, base64_to_wav
from services.language_manager import language_manager

class ASRService:
    """语音转写服务"""

    def __init__(self):
        """初始化语音转写服务"""
        self.api_key=Settings.OPENAI_API_KEY
        self.model = "whisper-1" # 默认使用whisper-1模型
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"
        self.timeout = 30.0 # 请求超时时间
    
    async def transcribe(self,audio_data:str,format:str="base64_adpcm") -> Dict[str,Any]:
        """
        将音频数据转写为文本
        
        Args:
            audio_data: 音频数据（ADPCM, PCM, WAV 等格式）
            format: 音频数据格式，默认为 "base64_adpcm"
            
        Returns:
            包含转写结果的字典：
            {
                "text": "转写文本",
                "language": "识别的语言代码",
                "confidence": 0.95,  # 置信度
                "is_final": True  # 是否为最终结果
            }
        """
        try:
            # 1.处理音频数据，转换为WAV格式
            wav_data = await self._prepare_audio(audio_data,format)

            # 2.调用Whisper API
            result = await self._call_whisper_api(wav_data)

            # 3.处理结果
            text = result.get("text","").strip()

            # 4. 检测语言(如果Whisper没有返回语言)
            language = result.get("language")
            if not language and text:
                language=detect_language(text)

            # 5. 标准化语言代码
            if language:
                language = normalize_language_code(language)
                # 6. 更新全局语言统计
                await language_manager.update_global_language_stats(language)

            # 7. 返回结果
            return {
                "text":text,
                "language":language,
                "confidence":result.get("confidence",0.0),
                "is_final":result.get("is_final",True)
            }
        except Exception as e:
            raise ASRException(f"ASR service error: {str(e)}")
        
    async def _prepare_audio(self,audio_data:str,format:str) -> bytes:
        """
        准备音频数据，转换为 WAV 格式
        
        Args:
            audio_data: 原始音频数据
            format: 音频格式
            
        Returns:
            WAV 格式的音频数据
        """
        try: 
            # 使用AudioConverter转换音频格式
            # wav_data = process_audio_to_wav(audio_data, source_format=format, sample_rate=16000)
            wav_data = base64_to_wav(audio_data, format=format, sample_rate=16000)

            return wav_data
        
        except Exception as e:
            raise ASRException(f"Audio preparation failed: {str(e)}")

    async def _call_whisper_api(self,wav_data:bytes) -> Dict[str,Any]:
        """
        调用 OpenAI Whisper API
        
        Args:
            wav_data: WAV 格式的音频数据
            
        Returns:
            API 响应结果
        """
        try: 
            # 创建临时WAV文件
            with tempfile.NamedTemporaryFile(delete=False,suffix=".wav") as temp_file:
                temp_file.write(wav_data)
                temp_file_path = temp_file.name
            
            try: 
                # 准备请求
                heards={
                    "Authorization":f"Bearer {self.api_key}",
                }

                files={
                    "file":("audio.wav",open(temp_file_path,"rb"),"audio/wav")
                }

                data={
                    "model":self.model,
                    "response_format":"verbose_json",
                }

                # 发送请求
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.api_url,
                        headers=heards,
                        files=files,
                        data=data,
                        timeout=self.timeout
                    )

                    if response.status_code != 200:
                        error_detail = response.text
                        try:
                            error_json = response.json()
                            if "error" in error_json:
                                error_detail = error_json["error"].get("message",error_json["error"])
                        except:
                            pass

                        raise ASRException(f"Whisper API error: {error_detail}")
                    
                    return response.json()
            finally:
                os.unlink(temp_file_path)
        
        except httpx.TimeoutException:
            raise ASRException("Whisper API request timed out")
        except Exception as e:
            if isinstance(e,ASRException):
                raise e
            raise ASRException(f"Whisper API call failed: {str(e)}")

    async def transcribe_streaming(self,audio_generator,format: str = "base64_adpcm") -> Dict[str,Any]:
        """
        流式转写（用于实时语音转写）
        
        Args:
            audio_generator: 音频数据生成器
            format: 音频数据格式
            
        Returns:
            转写结果
        """
        # 这里可以实现流式转写逻辑
        # 目前 OpenAI Whisper API 不支持流式转写，可以考虑分段处理
        # 或者使用其他支持流式转写的 API
        
        raise NotImplementedError("Streaming transcription is not implemented yet")
           
# 创建全局实例
asr_service = ASRService()
