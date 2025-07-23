from platform import system_alias
from typing import Dict,Any,List
import httpx
import json

from config.settings import Settings
from utils.sessions import Session
from utils.exceptions import IntentRecognitionException

class IntentRecognitionService:
    """
    意图识别服务
    """
    def __init__(self):
        self.api_key=Settings.OPENAI_API_KEY
        self.model="gpt-3.5-turbo"
        self.api_url= "https://api.openai.com/v1/chat/completions"
        self.timeout=15.0
        self.temperature=0.1

    async def analyze_intent(self,session:Session,text:str) -> Dict[str,Any]:
        """
        识别意图

        Args:
            session: 会话对象
            text: 用户输入的文本

        Returns:
            str: 意图识别结果
        """
        try: 
            # 构建会话历史
            history = self._build_conversation_history(session)

            # 调用OpenAI API进行意图识别
            result = await self._call_intent_api(history,text)

            return result

        except Exception as e:
            raise IntentRecognitionException(f"Intent recognition error: {e}")
    
    def _build_conversation_history(self,session:Session) -> List[Dict[str,str]]:
        """
        构建会话历史
        """
        history = []
        recent_conversations = session.conversation[-5:]

        for message in recent_conversations:
            history.append({
                "speaker":"user",
                "text":message.get("source_text","")
            })

        return history

    async def _call_intent_api(self,history:List[Dict],text:str) -> Dict[str,Any]:
        """调用OpenAI API进行意图识别"""
        
        system_prompt = """
# 角色
你是一个高度专业化的意图分类引擎。你的任务是结合对话历史，分析给定的当前文本，并判断该文本是否是一个**直接且可操作的翻译请求**。

# 核心任务
分析 `[History]` 和 `[Transcribed Text]`，并严格按照指定的JSON格式返回用户的真实意图。

# 输入格式
1.  `[History]`: 这是一个JSON数组，包含了最近的对话记录。它为你提供理解当前请求所必需的上下文。**此部分可能为空。**
2.  `[Transcribed Text]`: 这是用户当前说的、已知包含潜在翻译触发词的文本。

# 逻辑判断标准
1.  **优先分析历史记录**: 首先检查历史记录，理解对话的背景。用户的当前意图可能严重依赖于上一轮对话。
2.  **核心指导原则**:
    *   你的首要任务是识别出两个关键信息：**① 要被翻译的源文本 (Source Text)** 和 **② 目标语言 (Target Language)**。这两者中，至少有一个必须是明确的。当信息不完整时，你必须优先从 `[History]` 中寻找线索来补全。
3.  **判定为 `translate` 的条件**:
    #### A. 直接指令 (Direct Command)
    当用户的当前话语中同时包含了源文本和目标语言。
    *   **(规则)**: 用户的话语中包含一个明确的指令词（如“翻译”），并直接提供了需要翻译的内容和目标语言。
    *   **(例如)**: `"把‘早上好’翻译成西班牙语"` -> `source_text: "早上好"`, `target_language: "西班牙语"`

    #### B. 上下文追问与翻译链 (Contextual Follow-up & Translation Chaining) - 源文本隐含在历史中（最重要）
    当用户的当前话语非常简短，其核心内容（要翻译的文本）依赖于上一轮对话或更早的对话。

    *   **(规则 1)**: **翻译链追踪 (Translation Chain Tracking)**。当用户仅说出一个目标语言或一个指向语言的短语时（例如 "用日语说", "and in German?"），这表明一个翻译链正在继续。你的任务是：
        1.  **识别这是一个追问**：当前的用户输入是一个纯粹的语言指令。
        2.  **反向追溯历史**: 在 `[History]` 中反向查找，跳过所有中间的翻译指令（如“用印度语说”、“翻译成西班牙语”）。
        3.  **定位原始主语**: 找到启动这条“翻译链”的**最根本的、非指令性的文本**。这个“原始主语”就是你要找的 `source_text`。
    *   **(规则 2)**: **代词解析 (Pronoun Resolution)**。当用户使用代词（如 'it', 'that', '这个', '那个'）时，`source_text` 是该代词在 `[History]` 中所指向的具体内容。这通常是历史记录中最近的一条陈述性内容。

    #### C. 定义式查询 (Definition-style Query) - 目标语言隐含
    当用户查询某个词句的含义时，目标语言通常是对话的主要语言。
    *   **(规则)**: 用户使用“是什么意思”、“what does ... mean”等句式提问。`source_text` 是被查询的词句。如果未明确指定目标语言，则默认为本次对话的主要语言（如中文或英文）。

    #### D. 嵌入式指令 (Embedded Command)
    当翻译指令被包裹在一个更长的句子中时，你需要精准地剥离出指令和相关实体。
    *   **(规则)**: 忽略句子中的礼貌语、连接词或评论性内容，专注于提取核心的翻译请求。

4.  **判定为 `do_not_translate` 的条件**:
    *   **元语言讨论**: 用户在讨论翻译这个行为或词语本身。 (例如: "The word 'translate' is a verb.")
    *   **引用或转述**: 用户在引用别人的话。 (例如: "He said: 'translate this'.")
    *   **描述性或假设性陈述**: 用户在描述一个场景或提出一个假设。 (例如: "The button should say 'Translate to French'.")
    *   **上下文不符**: 即使有翻译关键词，但结合历史记录看，当前对话的主题与翻译无关。

# 输出要求
- **严格的JSON格式**: 你的输出**必须**是以下两种格式之一，绝无例外。
  - **当意图为 `translate` 时**:
  `{
    "intent": "translate",
    "source_text": "need to be translated text",
    "target_language": "target language"
  }`
  - **`source_text` 的关键规则**:
    - `source_text` 必须只包含纯粹需要翻译的内容。所有指令性短语（如 "翻译成", "how do you say", "帮我翻译" 等）都必须被彻底剥离。
    - `source_text` 绝不能包含任何指令性短语，例如 "翻译成", "translate", "how do you say", "translate it for me","是什么意思", "帮我翻译" 等等。你必须将这些指令部分从源文本中剥离出去
    - `source_text` 必须包含所有需要翻译的内容，不能遗漏任何部分。
    - `source_text` 必须准确反映用户想要翻译的原文内容。
    - `source_text` 必须准确反映用户意图的完整原文。无论是用户直接说出的，还是从历史记录中引用的，都不能有遗漏。
    - `source_text` 必须与用户当前的上下文相一致。
    - `source_text` 必须与用户当前的对话历史相一致。
    - `target_language` 必须是英文的缩写,并严格遵循BCP 47(Best Current Practice 47)标准同时注意按照大小写输出，例如 "zh-CN", "en-US", "ja-JP", "ko-KR", "fr-FR", "de-DE", "es-ES", "it-IT", "pt-PT", "ru-RU", "vi-VN", "ar-SA", "tl-PH"。
  - **当意图为 `do_not_translate` 时**:
  `{
    "intent": "do_not_translate",
    "source_text": "",
    "target_language": ""
  }`
- **禁止任何额外内容**: 你的回答中不能包含任何非JSON的文本。

# 工作流程示例

## 示例 1: 后续追问（最重要）
- **用户输入**:
  `[History]`
  `[{"speaker": "user", "text": "What is the capital of Japan?"}, {"speaker": "user", "text": "The capital of Japan is Tokyo."}]`
  `[Transcribed Text]`
  `"how do you say that in French?"`
- **你的最终输出**: 
`{
  "intent": "translate",
  "source_text": "The capital of Japan is Tokyo.",
  "target_language": "fr-FR"
}`

## 示例 2: 代词解析
- **用户输入**:
  `[History]`
  `[{"speaker": "user", "text": "I just wrote a new marketing slogan: 'Innovation that inspires'."}]`
  `[Transcribed Text]`
  `"Great, now translate it to Spanish."`
- **你的最终输出**: 
`{
  "intent": "translate",
  "source_text": "Innovation that inspires",
  "target_language": "es-ES"
}`

## 示例 3: 指令与内容在同一句中（最重要）
- **用户输入**:
  `[History]`
  `[]`
  `[Transcribed Text]`
  `"早上好,帮我翻译成西班牙语"`
- **你的最终输出**: 
`{
  "intent": "translate",
  "source_text": "早上好",
  "target_language": "es-ES"
}`

## 示例 4: 上下文消除歧义
- **用户输入**:
  `[History]`
  `[{"speaker": "user", "text": "Let's review the design of our translation app."}]`
  `[Transcribed Text]`
  `"I think the button 'translate to' is a bit confusing."`
- **你的最终输出**: `{"intent": "do_not_translate"}`

## 示例 5: 嵌入式指令
- **用户输入**:
  `[History]`
  `[]`
  `[Transcribed Text]`
  `"I'm not sure how to say 'hello' in Spanish. Can you help me?"`
- **你的最终输出**: 
`{
  "intent": "translate",
  "source_text": "hello",
  "target_language": "es-ES"
}`
"""
        user_prompt = f"""
[History]
{json.dumps(history, ensure_ascii=False)}

[Transcribed Text]
{text}
"""
        try:
            headers = {
                "Authorization":f"Bearer {self.api_key}",
                "Content-Type":"application/json"
            }

            data = {
                "model":self.model,
                "messages":[
                    {"role":"system","content":system_prompt},
                    {"role":"user","content":user_prompt}
                ],
                "temperature":self.temperature
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=data
                )

            if response.status_code !=200:
                raise IntentRecognitionException(f"Intent recognition API error: {response.status_code} {response.text}")

            result = response.json()
            
            if "choices" not in result or len(result["choices"]) == 0:
                raise IntentRecognitionException(f"Invalid API response: {result}")

            content = result["choices"][0]["message"]["content"].strip()
            
            intent_result = json.loads(content)

            return intent_result

        except json.JSONDecodeError:
            raise IntentRecognitionException("Intent recognition JSON decode error")
        except httpx.TimeoutException:
            raise IntentRecognitionException("Intent recognition request timeout")
        except Exception as e:
            raise IntentRecognitionException(f"Intent recognition API call failed: {str(e)}")

intent_recognition_service = IntentRecognitionService()