class Settings:
    # 应用基础设置
    APP_NAME: str = "MIC05 WebDemo API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "sqlite://./mic05.db"  # 默认SQLite，可改为PostgreSQL
    
    # 外部API密钥配置
    OPENAI_API_KEY: str = "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"
    
    # ASR服务配置（根据选择的服务）
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = ""
    GOOGLE_CLOUD_CREDENTIALS: str = ""  # JSON文件路径
    
    # 翻译服务配置
    AZURE_TRANSLATOR_KEY: str = ""
    AZURE_TRANSLATOR_REGION: str = ""
    GOOGLE_TRANSLATE_CREDENTIALS: str = ""
    
    # TTS服务配置
    AZURE_TTS_KEY: str = ""
    AZURE_TTS_REGION: str = ""
    GOOGLE_TTS_CREDENTIALS: str = ""
    
    # 系统默认设置
    DEFAULT_TARGET_LANGUAGE: str = "en"  # 默认目标语言
    SUPPORTED_LANGUAGES: list[str] = ["zh-CN", "en", "ja", "ko", "fr", "de", "es"]
    
    # WebSocket配置
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_TIMEOUT: int = 300
    
    # 音频处理配置
    MAX_AUDIO_SIZE: int = 10 * 1024 * 1024  # 10MB
    SUPPORTED_AUDIO_FORMATS: list[str] = ["wav", "mp3", "flac", "ogg"]
    AUDIO_SAMPLE_RATE: int = 16000
    
    # 文件存储配置
    UPLOAD_DIR: str = "./backend/uploads"
    EXPORT_DIR: str = "./backend/exports"
    MAX_EXPORT_FILES: int = 100
    
    # 缓存配置
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600  # 1小时
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "{time} | {level} | {message}"