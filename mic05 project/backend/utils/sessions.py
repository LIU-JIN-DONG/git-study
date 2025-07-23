from typing import List,Dict,Optional
from datetime import datetime
import uuid


class Session:
    """单次会话管理器"""
    def __init__(self,session_id:Optional[str]=None):
        self.session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        self.target_lang = ''
        self.detected_lang = ''
        self.session_langs:List[str] = []
        self.conversation = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def update_detected_lang(self,language:str) -> None:
        """"更新检测到的语言"""
        self.detected_lang = language
        # 更新会话语言数组
        if self.detected_lang in self.session_langs:
            self.session_langs.remove(self.detected_lang)
        self.session_langs.insert(0, str(self.detected_lang))
        self.updated_at = datetime.now()
    
    # TODO: 需不需要更新会话语言数组
    def update_target_lang(self,language:str) -> None:
        """更新目标语言"""
        self.target_lang = language

        # 更新会话语言数组
        if self.target_lang in self.session_langs:
            self.session_langs.remove(self.target_lang)
        self.session_langs.insert(0, str(self.target_lang))

        self.updated_at = datetime.now()

    async def set_target_language(self) ->None:
        """设置目标语言"""
        print(f"🔗 会话语言数组: {self.session_langs}")
        target_language = self.session_langs[0] if self.session_langs else ''

        from models.language_stats import LanguageStats
        
        if target_language==self.detected_lang:
            for lang in self.session_langs:
                if lang !=self.detected_lang:
                    target_language = lang
                    break
        print(f"🔗 通过会话数组获取的目标语言: {target_language}")

        if not target_language or target_language == '' or target_language == self.detected_lang:
            print(f"🔗 目标语言为空, 通过语言统计获取目标语言")
            languages = await LanguageStats.get_all_languages()
            for lang in languages:
                if lang != self.detected_lang:
                    target_language = lang
                    # 更新会话语言数组
                    self.session_langs.append(lang)
                    break
            
        self.target_lang = target_language
        self.updated_at = datetime.now()

    def add_to_conversation(self,transcript:str,translation:str,source_lang:str,target_lang:str,timestamp:str) ->None:
        """添加到会话历史"""
        self.conversation.append({
            "source_text":transcript,
            "target_text":translation,
            "source_language":source_lang,
            "target_language":target_lang,
            "timestamp":timestamp
        })
        self.updated_at = datetime.now()



class SessionManager:
    """会话管理器"""
    def __init__(self) -> None:
        self.sessions:Dict[str,Session] = {}

    def create_session(self,session_id:str) -> Session:
        """创建会话"""
        session = Session(session_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self,session_id:str) -> Optional[Session]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def delete_session(self,session_id:str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def get_all_sessions(self) -> Dict[str,Session]:
        """获取所有会话"""
        return self.sessions

session_manager = SessionManager()