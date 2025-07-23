from ssl import CHANNEL_BINDING_TYPES
from typing import Optional
from langdetect import DetectorFactory,detect, language
from utils.exceptions import LanguageDetectionException

DetectorFactory.seed = 0
def detect_language(text: str)->str:
    """检测文本的语言"""
    try:
        if not text or len(text.strip()) == 0:
            return "unknown"

        lang = detect(text)
        return normalize_language_code(lang)
    except Exception as e:
        raise LanguageDetectionException(f"Language detection failed: {str(e)}")

def normalize_language_code(lang:str)->str:
    """标准化语言代码"""
    lang_mapping = {
        "zh": "zh-CN", "zh-cn": "zh-CN", "zh-tw": "zh-TW","chinese": "zh-CN",
        "en": "en-US", "english": "en-US", "ja": "ja-JP", "japanese": "ja-JP", "ko": "ko-KR","korean": "ko-KR",
        "fr": "fr-FR", "french": "fr-FR", "de": "de-DE", "german": "de-DE", "es": "es-ES", "spanish": "es-ES",
        "it": "it-IT", "italian": "it-IT", "pt": "pt-PT", "portuguese": "pt-PT", "ru": "ru-RU", "russian": "ru-RU",
        "vi": "vi-VN","vietnamese": "vi-VN","ar": "ar-SA","arabic": "ar-SA","tl": "tl-PH","tagalog": "tl-PH"
    }
    return lang_mapping.get(lang.lower(),lang)

def get_language_name(lang:str,target_lang:str)->str:
    """获取语言名称"""
    language_names = {
        "zh-CN": {"en": "Chinese (Simplified)", "zh-CN": "简体中文"},
        "en-US": {"en": "English", "zh-CN": "英语"},
        "ja-JP": {"en": "Japanese", "zh-CN": "日语"},
        "ko-KR": {"en": "Korean", "zh-CN": "韩语"},
        "fr-FR": {"en": "French", "zh-CN": "法语"},
        "de-DE": {"en": "German", "zh-CN": "德语"},
        "es-ES": {"en": "Spanish", "zh-CN": "西班牙语"},
        "it-IT": {"en": "Italian", "zh-CN": "意大利语"},
        "pt-PT": {"en": "Portuguese", "zh-CN": "葡萄牙语"},
        "ru-RU": {"en": "Russian", "zh-CN": "俄语"},
        "ar-SA": {"en": "Arabic", "zh-CN": "阿拉伯语"},
        "vi-VN": {"en": "Vietnamese", "zh-CN": "越南语"},
        "tl-PH": {"en": "Tagalog", "zh-CN": "菲律宾语"}
    }
    normalized_language_code = normalize_language_code(lang)
    normalized_target_code = normalize_language_code(target_lang)
    lang_dict = language_names.get(normalized_language_code,{})
    return lang_dict.get(normalized_target_code,normalized_language_code)

def is_empty_or_whitespace(text:str)->bool:
    """判断文本是否为空或只包含空格"""
    return not text or text.strip() == ""

def truncate_text(text:str,max_length:int=100)->str:
    """截断文本"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..."
