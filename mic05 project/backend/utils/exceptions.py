from typing import Optional, Dict, List, Any


class BaseAPIException(Exception):
    """API异常基类"""
    def __init__(self, message: str = "An error occurred", code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class ASRException(BaseAPIException):
    """语音识别异常"""
    def __init__(self, message: str = "ASR service error", code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class TranslationException(BaseAPIException):
    """翻译服务异常"""
    def __init__(self, message: str = "Translation service error", code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class TTSException(BaseAPIException):
    """语音合成异常"""
    def __init__(self, message: str = "TTS service error", code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class LanguageDetectionException(BaseAPIException):
    """语言检测异常"""
    def __init__(self, message: str = "Language detection error", code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class AudioProcessingException(BaseAPIException):
    """音频处理异常"""
    def __init__(self, message: str = "Audio processing error", code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class SessionException(BaseAPIException):
    """会话管理异常"""
    def __init__(self, message: str = "Session management error", code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class DatabaseException(BaseAPIException):
    """数据库操作异常"""
    def __init__(self, message: str = "Database operation error", code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class GPTException(BaseAPIException):
    """GPT服务异常"""
    def __init__(self, message: str = "GPT service error", code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class IntentRecognitionException(BaseAPIException):
    """意图识别异常"""
    def __init__(self, message: str = "Intent recognition error", code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class TitleGenerationException(BaseAPIException):
    """标题生成异常"""
    def __init__(self, message: str = "Title generation error", code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

def handle_exception(e: Exception) -> dict:
    """处理异常并返回统一格式的错误响应"""
    if isinstance(e, BaseAPIException):
        return {
            "code": e.code,
            "message": e.message,
            "details": e.details
        }
    # 处理其他类型的异常
    return {
        "code": 500,
        "message": str(e),
        "details": {"type": e.__class__.__name__}
    }