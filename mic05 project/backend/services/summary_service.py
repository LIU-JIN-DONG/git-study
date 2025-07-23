from typing import Dict
import os
from pathlib import Path
import re
from typing import Optional,List,Dict,Any
import httpx
from datetime import datetime

from config.settings import Settings
from utils.exceptions import GPTException
from utils.sessions import Session
from models.history import History

class SummaryService:
    """
    总结服务，使用OpenAI API 生成总结
    """

    def __init__(self):
        self.api_key = Settings.OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        self.timeout = 60
        self.temperature = 0.7

        # 导出目录
        self.export_dir = Path(Settings.EXPORT_DIR or "./backend/exports")
        # 确保目录存在
        self.export_dir.mkdir(exist_ok=True, parents=True)

        self.max_export_files=Settings.MAX_EXPORT_FILES or 100

    async def generate_summary(self,session_id:str,session:Optional[Session]=None,language:str="english")->str:
        """
        生成总结

        Args:
            session: 会话对象
            session_id: 会话ID

        Returns:
            总结文本
        """
        try:
            # 获取会话数据
            if session:
                conversations = session.conversation
            else:
                history = await History.get_by_session_id(session_id)
                if history:
                    conversations = history.conversation
                else:
                    raise GPTException("No session_id provided")

            # 生成总结：
            if isinstance(conversations, dict):
                conversations = [conversations]
            summary = await self._generate_summary_with_gpt(conversations,language)

            # 更新会话总结
            await History.update_summary(session_id,summary)

            return summary
        
        except Exception as e:
            raise GPTException(f"Failed to generate summary: {str(e)}")
            
    async def _generate_summary_with_gpt(self,conversations:List[Dict],language:str="english") -> str:
        """
        使用GPT生成总结

        Args:
            conversations: 对话数据

        Returns:
            总结文本
        """
        try:
            # 构建对话内容
            conversation_text = self._format_conversations(conversations)

            # 构建系统提示
            system_prompt = f"""
# 角色
你是一位资深的**会话分析师**和**语言故事家**。你的任务不仅仅是总结，而是要将一段翻译会话，提炼成一份精美、深刻且对用户极具价值的回顾报告。

# 核心任务
分析给定的会话文本，并使用指定的语言 ({language}) 生成一份结构清晰、语言优美、充满洞察力的Markdown格式总结。

# 输出结构与要求
请严格遵循以下结构，并确保每个部分都内容翔实、重点突出：

### 1. 会话快照 (Conversation Snapshot) 
*   **核心信息**: 简要说明会话的时间、时长（如果可知）、涉及的主要语言。
*   **核心目标**: 一句话概括本次会话的主要目的或探讨的核心问题。

### 2. 对话亮点 (Conversation Highlights) 
*   **叙事性总结**: 不要简单罗列，而是像讲故事一样，描述对话是如何开始、发展、并达到关键点的。
*   **关键问答**: 提取1-3个最核心的问答对或交流片段。

### 3. 语言洞察 (Language Insights) 
*   **交流动态**: 描述两种语言的使用频率和切换情况。例如：“本次对话以中文开始，在探讨技术细节时，频繁切换到英文术语。”
*   **词汇复杂度**: 评价使用的词汇是偏向日常，还是专业领域。

### 4. 知识点提炼 (Knowledge Gems) 
*   **这是最重要的部分**。请发掘并列出具体的语言学习点，例如：
    *   **地道表达**: 某个词或短语更地道的说法。
    *   **文化注释**: 某个表达背后可能存在的文化背景。
    *   **语法提示**: 对话中出现的不易察觉的语法点或常见错误。
    *   **同义词/近义词**: 提供了哪些词语的更多表达方式。

### 5. 总结与鼓励 (Summary & Encouragement) 
*   用一两句积极的话总结这次会话的成果，并鼓励用户在语言学习上继续进步。

# 风格指南
*   **语言优美**: 使用生动、流畅、富有感染力的语言。
*   **格式清晰**: 善用Markdown的加粗、列表、引用块等功能，让报告易于阅读。
*   **富有洞察**: 展现你作为语言专家的分析能力，提供超越字面内容的价值。
*   **语言**: 使用{language}语言输出。

# 工作示例 (Working Example)
下面是一个如何根据指令生成指定语言报告的例子。

---
[输入]
- **指定语言**: English
- **会话记录**:
用户: 你好
AI: Hello
用户: 帮我把“我爱编程”翻译成英文
AI: I love programming.

[期望的输出]
### Conversation Snapshot 
*   **Core Info**: This was a brief session involving Chinese and English.
*   **Core Objective**: The user's primary goal was to translate a specific phrase.

### Dialogue Highlights 
The conversation started with a simple greeting exchange. The user then directly requested the translation of "我爱编程" (I love programming), which the AI successfully provided.

... (此处省略更多英文总结内容)
---

# 你的任务
现在，请根据下面的会话记录，严格模仿上面的示例，用 `{language}` 语言生成一份全新的报告。
"""


            user_prompt = f"""
请为以下翻译会话生成一份精美的总结报告。

[Conversation]
{conversation_text}

[Language]
{language}
"""
            
            messages = [
                {"role":"system","content":system_prompt},
                {"role":"user","content":user_prompt}
            ]

            # 调用API
            response = await self._call_gpt_api(messages)

            return response
            
        except Exception as e:
            raise GPTException(f"Failed to generate summary: {str(e)}")

    def _format_conversations(self,conversations:List[Dict]) -> str:
        """
        格式化对话内容

        Args:
            conversations: 对话数据

        Returns:
            格式化后的对话内容
        """
        formatted_lines = []

        for i,conv in enumerate(conversations):
            transcript = conv.get("source_text","")
            translation = conv.get("target_text","")
            source_lang = conv.get("source_language","")
            target_lang = conv.get("target_language","")

            formatted_lines.append(f"session {i+1}:")
            formatted_lines.append(f"  text ({source_lang}): {transcript}")
            formatted_lines.append(f"  translation ({target_lang}): {translation}")
            formatted_lines.append("")

        return "\n".join(formatted_lines)
    
    async def _call_gpt_api(self,messages:List[Dict]) -> str:
        """
        调用GPT API

        Args:
            messages: 对话消息列表

        Returns:
            API响应内容
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": 1000
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=data
                )

            if response.status_code !=200: 
                error_detail = response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_detail = error_json["error"].get("message", error_json["error"])
                except:
                    pass
                
                raise GPTException(f"API request failed with status {response.status_code}: {error_detail}")
            
            result = response.json()

            if "choices" not in result or len(result["choices"]) == 0:
                raise GPTException("Invalid API response: missing choices")

            summary = result["choices"][0]["message"]["content"].strip()

            return summary

        except httpx.TimeoutException:
            raise GPTException(f"API request timed out after {self.timeout} seconds")
        except Exception as e:
            if isinstance(e, GPTException):
                raise e
            raise GPTException(f"GPT API request failed: {str(e)}")

    async def export_to_markdown(self,summary:str,session_id:str,filename:Optional[str]=None)->Dict[str,str]:
        """
        将会话导出为Markdown格式

        Args:
            session: 会话对象
            filename: 文件名

        Returns:
            包含文件名和文件路径的映射
        """
        try:
            # 生成文件名
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                session_part=f"_{session_id}" if session_id else ""
                filename = f"summary_{timestamp}{session_part}.md"

            #  确保是md文件
            if not filename.endswith(".md"):
                filename += ".md"

            # 创建导出目录
            file_path = self.export_dir / filename

            # 生成Markdown内容
            markdown_content = self._create_markdown_content(summary,session_id)

            # 写入文件
            with open(file_path,"w",encoding="utf-8") as f:
                f.write(markdown_content)

            # 清理过期文件
            await self._cleanup_old_files()    

            # 计算相对路径，处理可能的路径问题
            try:
                relative_path = str(file_path.relative_to(Path.cwd()))
            except ValueError:
                # 如果无法计算相对路径，使用绝对路径
                relative_path = str(file_path)

            return {
                "filename":filename,
                "path": str(file_path),
                "relative_path": relative_path,
                "size": str(os.path.getsize(file_path)),
                "created_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            raise GPTException(f"Failed to export to markdown: {str(e)}")

    def _create_markdown_content(self,summary:str,session_id:str) -> str:
        """
        创建Markdown内容

        Args:
            summary: 总结文本
            session_id: 会话ID

        Returns:
            Markdown内容
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        markdown_lines = [
            "# Summary on Details",
            "",
            f"**Created At:** {current_time}",
        ]

        if session_id:
            markdown_lines.append(f"**Session ID:** {session_id}")

        markdown_lines.extend([
            "",
            "---",
            "",
            "## Summary Content:",
            "",
            summary,
            "",
            "---",
            "",
            f"*Generated by MIC05 WebDemo @ hearit.ai*"
        ])

        return "\n".join(markdown_lines)

    async def _cleanup_old_files(self):
        """清理旧的导出文件"""
        try:
            # 获取所有导出文件
            export_files = list(self.export_dir.glob("*.md"))

            # 如果文件数量超过限制，删除最旧的文件
            if len(export_files) > self.max_export_files:
                # 按修改时间排序
                export_files.sort(key=lambda x: os.path.getmtime(x))

                # 删除最旧的文件
                files_to_delete = export_files[:-self.max_export_files]
                for file_path in files_to_delete:
                    try:
                        file_path.unlink()
                        print(f"Deleted old export file: {file_path}")
                    except Exception as e:
                        print(f"Failed to delete old export file {file_path}: {str(e)}")
        
        except Exception as e:
            print(f"Failed to cleanup old exports: {str(e)}")
    async def generate_and_export_summary(self,session_id:str,language:str="english",session:Optional[Session]=None,filename:Optional[str]=None)->Dict[str,Any]:
        """
        生成总结并导出为文件
        
        Args:
            session_id: 会话ID
            filename: 自定义文件名
            
        Returns:
            包含总结和文件信息的字典
        """
        try:
            #生成总结
            summary = await self.generate_summary(session_id,session,language)

            # 导出为Markdown
            file_info = await self.export_to_markdown(summary,session_id,filename)

            return {
                "summary":summary,
                "file_info":file_info,
                "success":True
            }
        
        except Exception as e:
            raise GPTException(f"Failed to generate and export summary: {str(e)}")

    async def get_exported_files(self)->List[Dict[str,Any]]:
        """
        获取所有导出文件

        Returns:
            包含文件信息的列表
        """
        try:
            files = []
            for file_path in self.export_dir.glob("*.md"):
                stat = file_path.stat()
                files.append({
                    "filename":file_path.name,
                    "path":str(file_path),
                    "size":stat.st_size,
                    "created_at":datetime.fromtimestamp(stat.st_ctime).isoformat()
                })

            # 按修改时间倒序排列
            files.sort(key=lambda x: x["created_at"], reverse=True)

            return files
        
        except Exception as e:
            raise GPTException(f"Failed to get exported files: {str(e)}")
        
summary_service = SummaryService()
        
    
