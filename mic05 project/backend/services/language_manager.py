from typing import Dict
from logging import exception
from typing import List,Union,Optional,Any
import asyncio
from datetime import datetime

from utils.exceptions import SessionException
from utils.sessions import Session
from utils.language_utils import normalize_language_code
from models.language_stats import LanguageStats

class LanguageManager:
    """语言管理器"""

    def __init__(self):
        """初始化语言管理器"""
        pass


    async def update_target_language(self,session:Session) -> None:
        """获取目标语言"""
        try:
            await session.set_target_language()
        
        except Exception as e:
            raise SessionException(f"Failed to get target language: {str(e)}")
         
    async def update_session_language(self,session:Session,detect_language:str) -> None:
        """
        更新会话语言

        Args:
            detect_language: 检测到的语言代码
        """
        try: 
            normalized_lang = normalize_language_code(detect_language)

            session.update_detected_lang(normalized_lang)

        except Exception as e:
            raise SessionException(f"Failed to update session language: {str(e)}")

    async def update_global_language_stats(self,language:str) ->None:
        """
        更新全局语言统计

        Args:
            language: 要更新的语言代码
        """
        try:
            normalized_lang = normalize_language_code(language)
            await LanguageStats.increment_usage(normalized_lang)
            print(f"Global language stats updated: {normalized_lang}")
        
        except Exception as e:
            raise SessionException(f"Failed to update global language stats: {str(e)}")

    async def get_translation_language_pair(self,session:Session) -> Dict[str,str]:
        """获取翻译语言对"""
        try:
            source_language = session.detected_lang
            target_language = session.target_lang
            return {
                "source_language": source_language,
                "target_language": target_language,
            }
        
        except Exception as e:
            raise SessionException(f"Failed to get translation language pair: {str(e)}")
language_manager = LanguageManager()