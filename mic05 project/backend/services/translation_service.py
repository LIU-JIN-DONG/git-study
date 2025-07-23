import json
import httpx
from typing import Dict, Any, List
from datetime import datetime

from config.settings import Settings
from services.language_manager import language_manager
from utils.language_utils import normalize_language_code
from utils.sessions import Session
from utils.exceptions import TranslationException

class TranslationService:
    """翻译服务"""

    def __init__(self):
        """初始化翻译服务"""
        self.api_key = Settings.OPENAI_API_KEY
        self.model = "gpt-3.5-turbo" # 默认使用gpt-3.5-turbo模型
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.timeout = 30.0
        self.temperature = 0.3 # 较低的温度，保证翻译的精准性
    
    async def translate(self,session:Session,text:str,detect_language:str,target_lang:str) ->Dict[str,Any]:
        """
        翻译文本
        
        Args:
            text: 要翻译的文本
            detected_lang: 检测到的语言
            
        Returns:
            包含翻译结果的字典：
            {
                "source_text": "原文",
                "target_text": "翻译后的文本",
                "source_lang": "源语言",
                "target_lang": "目标语言",
                "confidence": 0.95  # 翻译的置信度
            }
        """
        try:
            # 1. 更新会话语言
            await language_manager.update_session_language(session,detect_language)

            # 2. 获取目标语言
            if not target_lang:
                await language_manager.update_target_language(session)
                translation_language_pair = await language_manager.get_translation_language_pair(session)
                source_language = translation_language_pair["source_language"]
                target_language = translation_language_pair["target_language"]
            else:
                source_language = detect_language
                target_lang = normalize_language_code(target_lang)
                target_language = target_lang

            # 3. 调用 OpenAI API 进行翻译
            result = await self._translate_with_openai(session,text,source_language,target_language)

            # 4. 处理翻译结果
            return {
                "source_text": text,
                "target_text": result.get("translation"),
                "source_language": source_language,
                "target_language": target_language,
                "confidence": result.get("confidence",0.95)
            }

        except Exception as e:
            raise TranslationException(f"Failed to translate text: {str(e)}")
            
    async def _translate_with_openai(self,session:Session,text:str,source_lang:str,target_lang:str) -> Dict[str,Any]:
        """
        使用OpenAI API进行翻译
        
        Args:
            text: 要翻译的文本
            source_lang: 源语言
            target_lang: 目标语言

        Returns:
            包含翻译结果的字典：
            {
                "translation": "翻译后的文本",
                "confidence": 0.95  # 翻译的置信度
            }
        """
        try:
            # 构建消息列表
            message = []

            # prompts
            system_message = f"""
# 角色
你是一个高度专业化的翻译引擎。你的唯一任务是根据提供的上下文历史，将当前文本精准地翻译成目标语言。你必须像一个API一样工作，只返回结果，不返回任何解释或无关的文本。

# 核心任务
你的任务是翻译 `[当前文本]` 区域的内容到 `[目标语言]` 指定的语言。

# 输入格式
你将接收到以下三个部分的信息：
1.  `[历史记录]`: 这是一个包含过去对话转录和翻译的记录。这些信息是为你提供上下文参考的，以确保术语、风格和语气的连贯性和一致性。**此部分可能为空。**
2.  `[当前文本]`: 这是当前需要被翻译的一段或几段文字。
3.  `[目标语言]`: 这是你必须将 `[当前文本]` 翻译成的语言。

# 关键指令
1.  **分析历史记录**：仔细分析 `[历史记录]` 以理解对话的背景、特定术语（如人名、产品名、专业词汇）的固定翻译方式和整体的沟通风格。
2.  **处理空历史**：如果 `[历史记录]` 为空，则将其视为没有可用上下文。在这种情况下，你必须直接、独立地翻译 `[当前文本]`，无需进行任何基于历史的上下文推断。
3.  **不要翻译历史记录**：`[历史记录]` 仅供参考，你绝对不能翻译或复述这部分内容。
4.  **专注翻译当前文本**：你的全部注意力都应该放在将 `[当前文本]` 的内容翻译成 `[目标语言]` 上。
5.  **保持一致性**：当历史记录存在时，利用从中学到的知识，确保你的翻译在术语和风格上与之前的翻译保持高度一致。

# 输出要求
- **直接输出**：你的输出必须且只能是 `[当前文本]` 翻译后的内容。
- **不要包含标签**：不要在你的回答中包含如 `翻译结果:` 或 `[Translated Text]:` 之类的标签。
- **绝不添加任何额外文本**：禁止添加任何前缀、后缀、问候语、解释、道歉、注释或任何形式的元评论。你的输出必须是纯粹、干净的翻译文本。

# 工作流程示例

## 示例 1: 有历史记录
- **输入**:
  `[历史记录]`
  - 原文: "Our key product is called 'ShadowCat'."
  - 译文: "我们的核心产品叫做‘影猫’。"
  `[当前文本]`
  "Let's discuss the marketing strategy for ShadowCat."
  `[目标语言]`
  中文
- **你的思考过程 (内部)**:
  1.  从历史记录中得知 "ShadowCat" 的官方翻译是 "影猫"。
  2.  当前文本需要翻译 "Let's discuss the marketing strategy for ShadowCat."。
  3.  我需要将 "ShadowCat" 翻译为 "影猫"，而不是“影子猫”或其他。
  4.  最终翻译是“我们来讨论一下影猫的营销策略吧。”
- **你的最终输出 (必须如此)**:
  我们来讨论一下影猫的营销策略吧。

## 示例 2: 历史记录为空
- **输入**:
  `[历史记录]`

  `[当前文本]`
  "The quick brown fox jumps over the lazy dog."
  `[目标语言]`
  中文
- **你的思考过程 (内部)**:
  1.  历史记录为空，没有可用的上下文。
  2.  我需要独立地、标准地翻译 "The quick brown fox jumps over the lazy dog."。
  3.  最终翻译是“敏捷的棕色狐狸跳过懒惰的狗。”
- **你的最终输出 (必须如此)**:
  敏捷的棕色狐狸跳过懒惰的狗。
"""

            user_message = f"""
[历史记录]
{session.conversation}

[当前文本]
{text}

[目标语言]
{target_lang}
"""

            message.append({"role":"system","content":system_message})

            message.append({"role":"user","content":user_message})

            # 构建请求数据
            headers ={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model":self.model,
                "messages":message,
                "temperature":self.temperature
            }
            # 调用OpenAI API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
            
            if response.status_code != 200:
                error_detail= response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_detail = error_json["error"].get("message",error_json["error"])
                except:
                    pass
                raise TranslationException(f"API request failed with status {response.status_code}: {error_detail}")

            result = response.json()

            if "choices" not in result or len(result["choices"]) == 0:
                raise TranslationException("Invalid API response format")

            content = result["choices"][0]["message"]["content"]

            # 解析响应文本
            try:
                translation_result = json.loads(content)
                return translation_result
            except json.JSONDecodeError:
                # 如果不是有效的 JSON，尝试提取翻译结果
                return {
                    "translation": content.strip(),
                    "confidence": 0.95
                }
            
                
        except httpx.TimeoutException:
            raise TranslationException(f"API request timed out after {self.timeout} seconds")
        except Exception as e:
            if isinstance(e, TranslationException):
                raise e
            raise TranslationException(f"Translation API request failed: {str(e)}")

    async def translate_and_save(self,session:Session,text:str,detected_lang:str,target_lang:str) -> Dict[str,Any]:
        """
        翻译并保存翻译结果
        
        Args:
            text: 要翻译的文本
            detected_lang: 检测到的语言

        Returns:
            翻译结果
        """
        result = await self.translate(session,text,detected_lang,target_lang)

        session.add_to_conversation(
            transcript=result["source_text"],
            translation=result["target_text"],
            source_lang=result["source_language"],
            target_lang=result["target_language"],
            timestamp=datetime.now().isoformat()
        )

        return result
    
    async def get_supported_languages(self) -> List[Dict[str,str]]:
        """
        获取支持的语言列表
        
        Returns:
            支持的语言列表
        """
        languages = [
            {"code": "zh-CN", "name": "简体中文", "english_name": "Chinese (Simplified)"},
            {"code": "en-US", "name": "英语", "english_name": "English"},
            {"code": "ja-JP", "name": "日语", "english_name": "Japanese"},
            {"code": "ko-KR", "name": "韩语", "english_name": "Korean"},
            {"code": "fr-FR", "name": "法语", "english_name": "French"},
            {"code": "de-DE", "name": "德语", "english_name": "German"},
            {"code": "es-ES", "name": "西班牙语", "english_name": "Spanish"},
            {"code": "it-IT", "name": "意大利语", "english_name": "Italian"},
            {"code": "ru-RU", "name": "俄语", "english_name": "Russian"},
            {"code": "pt-PT", "name": "葡萄牙语", "english_name": "Portuguese"},
            {"code": "ar-SA", "name": "阿拉伯语", "english_name": "Arabic"},
            {"code": "vi-VN", "name": "越南语", "english_name": "Vietnamese"},
            {"code": "tl-PH", "name": "菲律宾语", "english_name": "Tagalog"}
        ]

        return languages
    
translation_service = TranslationService()
