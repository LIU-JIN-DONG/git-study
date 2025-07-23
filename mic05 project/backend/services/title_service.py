import httpx
import json
from typing import Optional,Tuple

from config.settings import Settings
from models.history import History
from utils.exceptions import TitleGenerationException

class TitleService:
    """
    标题生成服务
    """
    def __init__(self):
        self.api_key=Settings.OPENAI_API_KEY
        self.model="gpt-4o-mini"
        self.api_url="https://api.openai.com/v1/chat/completions"
        self.timeout=15.0
        self.temperature=0.1

    async def generate_title(self,session_id:str,max_length:int=20) -> None:
        """
        生成标题

        Args:
            session_id: 会话ID
            max_length: 标题最大长度

        Returns:
            Optional[str]: 生成的标题
        """
        try:
            # 获取会话历史
            history = await History.get_by_session_id(session_id)
            if not history:
                return None
            
            conversation = history.conversation
            if not conversation:
                return None
            
            # 系统提示词
            system_prompt = """
# 角色
你是一个高效的AI助手，专门负责分析、总结和分类会话记录。

## 你的任务
根据我提供的JSON格式的会话历史记录，你需要完成以下两项工作：
1.  为该会话生成一个简短、精炼、能准确概括对话核心内容的**英文标题 (English Title)**。
2.  从我提供的固定分类列表中，为该会话选择一个最合适的分类。

## 输入格式说明
我提供的输入将是一个JSON对象，其中包含一个名为 `records` 的列表。
*   `records` 列表中的每一项都是一个独立的翻译记录对象。
*   你需要分析每个记录对象中的 `source_text` 和 `target_text` 字段来理解完整的对话内容。
*   请按 `records` 列表的顺序，将所有文本串联起来，以把握对话的上下文和流程。

## 核心指令
1.  **标题 (Title)**:
    *   必须是一个简短的**英文**短语，而不是一个完整的句子。
    *   它应该抓住对话的要点。
2.  **分类 (Category)**:
    *   **必须**从下面提供的11个类别中选择**一个**最贴切的。
    *   不允许使用此列表之外的任何分类。
    *   输出分类时，**不要包含**任何数字或标点符号，只输出类别名称本身。

### 分类列表 (必须从此列表中选择)
[
  "Casual",
  "Travel",
  "Business",
  "Shopping",
  "Food",
  "Entertainment",
  "Education",
  "Technology",
  "Medical",
  "Legal",
  "Emergency"
]

## 输出格式
你的输出**必须严格**按照以下json格式，不要添加任何额外的解释、介绍或说明文字。
{
    "title": "Your Generated English Title",
    "category": "Your Selected Category"
}


---

## 示例

### 示例 1
**输入:**
```json
{
    "records": [
        {
            "id": "record_001",
            "timestamp": "2025-07-14T18:16:15.905267",
            "source_text": "你好,今天是星期幾",
            "target_text": "What day is it today?",
            "source_language": "zh-CN",
            "target_language": "en-US"
        },
        {
            "id": "record_002",
            "timestamp": "2025-07-14T18:16:29.719950",
            "source_text": "Hello, hello, my name is Mike.",
            "target_text": "你好，你好，我叫迈克。",
            "source_language": "en-US",
            "target_language": "zh-CN"
        }
    ]
}
```

**预期输出:**
{
    "title": "Basic Greetings and Introduction",
    "category": "Casual"
}


### 示例 2
**输入:**
```json
{
    "records": [
        {
            "id": "record_a",
            "source_text": "你好，请问去希尔顿酒店怎么走？",
            "target_text": "Hi, how do I get to the Hilton Hotel?"
        },
        {
            "id": "record_b",
            "source_text": "Go straight for two blocks then turn left.",
            "target_text": "直走两个街区然后左转就到了。"
        },
        {
            "id": "record_c",
            "source_text": "非常感谢！我想要办理入住。",
            "target_text": "Thanks! I'd like to check in."
        }
    ]
}
```

**预期输出:**
{
    "title": "Hotel Check-in and Directions",
    "category": "Travel"
}

### 示例 3
**输入:**
```json
{
    "records": [
        {
            "id": "rec_x",
            "source_text": "我们必须紧急修复登录页面的那个bug。",
            "target_text": "We must urgently fix the bug on the login page."
        },
        {
            "id": "rec_y",
            "source_text": "Yes, this issue is causing a high user drop-off rate.",
            "target_text": "是的，这个问题导致了很高的用户流失率。"
        },
        {
            "id": "rec_z",
            "source_text": "I've located the root cause. It's an authentication logic error in the backend API.",
            "target_text": "我已经定位到问题根源了，是后端API的一个认证逻辑错误。"
        }
    ]
}
```

**预期输出:**
```
{
    "title": "Urgent Login Page Bug Fix",
    "category": "Technology"
}
```
"""
            # 用户提示词
            user_prompt = f"""
```json
{json.dumps(conversation,ensure_ascii=False)}
```
            """

            # 准备请求数据
            header = {
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
                    headers=header,
                    json=data
                )

            if response.status_code !=200:
                raise TitleGenerationException(f"Title generation API error: {response.status_code} {response.text}")

            result = response.json()
            if "choices" not in result or len(result["choices"]) == 0:
                raise TitleGenerationException(f"Invalid API response: {result}")
            
            content = result["choices"][0]["message"]["content"].strip()
            title_result = json.loads(content)

            
            # 更新会话历史,保存到数据库
            title = title_result.get("title",None)
            category = title_result.get("category",None)

            history.title = title
            history.category = category
            await history.save()

        except json.JSONDecodeError:
            raise TitleGenerationException("Title generation JSON decode error")

title_service = TitleService()