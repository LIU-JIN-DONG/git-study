import asyncio
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import uuid
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.summary_service import SummaryService, summary_service
from backend.utils.exceptions import GPTException
from backend.utils.sessions import Session
import httpx


async def check_api_key(api_key: str) -> bool:
    """验证OpenAI API密钥是否有效"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 使用models端点来验证密钥
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers=headers
            )
            
        return response.status_code == 200
    except Exception as e:
        print(f"API密钥验证错误: {e}")
        return False


class TestSummaryService:
    """总结服务测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.summary_service = SummaryService()
        
        # 创建模拟会话数据
        self.mock_session = Session()
        self.mock_session.session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        
        # 添加丰富的对话数据
        self.mock_session.conversation = [
            {
                "transcript": "你好，今天天气怎么样？",
                "translation": "Hello, how's the weather today?",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "timestamp": datetime.now().isoformat()
            },
            {
                "transcript": "It's quite sunny and warm today, perfect for outdoor activities.",
                "translation": "今天阳光明媚，很温暖，非常适合户外活动。",
                "source_lang": "en-US",
                "target_lang": "zh-CN",
                "timestamp": datetime.now().isoformat()
            },
            {
                "transcript": "那太好了！我想去公园散步。",
                "translation": "That's great! I want to go for a walk in the park.",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "timestamp": datetime.now().isoformat()
            },
            {
                "transcript": "Would you like to join me? We could have a picnic there.",
                "translation": "你愿意和我一起去吗？我们可以在那里野餐。",
                "source_lang": "en-US",
                "target_lang": "zh-CN",
                "timestamp": datetime.now().isoformat()
            },
            {
                "transcript": "听起来很不错！我会准备一些食物。",
                "translation": "That sounds wonderful! I'll prepare some food.",
                "source_lang": "zh-CN",
                "target_lang": "en-US",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # 确保test文件夹存在
        self.test_dir = Path("backend/test")
        self.test_dir.mkdir(exist_ok=True)

    @pytest.mark.asyncio
    async def test_generate_summary_with_mock(self):
        """测试生成总结（使用模拟数据）"""
        # 模拟GPT API响应
        mock_summary = """# 会话总结

## 会话概览
- **时间**: 2024年测试会话
- **参与语言**: 中文(zh-CN) ↔ 英文(en-US)
- **主要话题**: 天气讨论和户外活动计划

## 关键对话内容摘要
本次会话是一个关于天气和户外活动的友好对话。对话从询问天气开始，发展到计划公园散步和野餐的讨论。

## 语言使用统计
- 中文消息: 3条
- 英文消息: 2条
- 总翻译次数: 5次

## 主要讨论话题
1. 天气状况 - 晴朗温暖的天气
2. 户外活动 - 公园散步计划
3. 社交邀请 - 邀请一起参加活动
4. 活动准备 - 野餐食物准备

## 语言学习点
- 天气相关词汇: "sunny", "warm", "阳光明媚"
- 活动邀请表达: "Would you like to join me?"
- 积极回应: "That sounds wonderful!"

这是一个很好的日常对话练习，涵盖了天气、邀请和计划等常用话题。"""

        with patch('httpx.AsyncClient') as mock_client:
            # 设置模拟响应
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": mock_summary
                        }
                    }
                ]
            }
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # 执行总结生成
            result = await self.summary_service.generate_summary(self.mock_session)
            
            # 验证结果
            assert result == mock_summary
            assert "会话总结" in result
            assert "天气" in result
            assert "户外活动" in result
            
            print(f"✅ 总结生成测试完成！")
            print(f"📝 生成的总结长度: {len(result)} 字符")

    @pytest.mark.asyncio
    async def test_export_to_markdown(self):
        """测试导出为Markdown文件"""
        # 模拟总结内容
        mock_summary = """# 测试会话总结

这是一个测试总结，包含了会话的主要内容和分析。

## 主要话题
- 天气讨论
- 户外活动计划
- 社交邀请

## 语言统计
- 中文: 3条消息
- 英文: 2条消息
"""

        # 执行导出
        result = await self.summary_service.export_to_markdown(
            summary=mock_summary,
            session=self.mock_session,
            filename="test_summary"
        )
        
        # 验证结果
        assert "filename" in result
        assert "path" in result
        assert result["filename"].endswith(".md")
        
        # 验证文件是否创建
        file_path = Path(result["path"])
        assert file_path.exists()
        assert file_path.stat().st_size > 0
        
        # 读取文件内容验证
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Summary on Details" in content
            assert "测试会话总结" in content
            assert "MIC05 WebDemo @ hearit.ai" in content
        
        print(f"✅ Markdown导出测试完成！")
        print(f"📁 文件路径: {result['path']}")
        print(f"📊 文件大小: {result['size']} bytes")

    @pytest.mark.asyncio
    async def test_generate_and_export_summary_with_mock(self):
        """测试生成并导出总结（使用模拟数据）"""
        mock_summary = """# 完整会话总结

## 会话信息
- 会话ID: """ + self.mock_session.session_id + """
- 消息数量: 5条
- 语言对: 中文 ↔ 英文

## 内容摘要
这是一个关于天气和户外活动的对话，展现了良好的语言交流。

## 学习价值
包含了日常对话中的常用表达和词汇。"""

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": mock_summary
                        }
                    }
                ]
            }
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # 执行生成和导出
            result = await self.summary_service.generate_and_export_summary(
                session=self.mock_session,
                filename="complete_test_summary"
            )
            
            # 验证结果
            assert result["success"] is True
            assert "summary" in result
            assert "file_info" in result
            assert result["summary"] == mock_summary
            
            # 验证文件信息
            file_info = result["file_info"]
            assert file_info["filename"].endswith(".md")
            assert Path(file_info["path"]).exists()
            
            print(f"✅ 完整总结生成和导出测试完成！")
            print(f"📝 总结内容: {result['summary'][:100]}...")
            print(f"📁 导出文件: {file_info['filename']}")

    def test_format_conversations(self):
        """测试对话格式化"""
        formatted = self.summary_service._format_conversations(self.mock_session.conversation)
        
        # 验证格式化结果
        assert "session 1:" in formatted
        assert "你好，今天天气怎么样？" in formatted
        assert "Hello, how's the weather today?" in formatted
        assert "zh-CN" in formatted
        assert "en-US" in formatted
        
        print(f"✅ 对话格式化测试完成！")
        print(f"📄 格式化内容预览:\n{formatted[:200]}...")

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        # 创建空会话
        empty_session = Session()
        empty_session.conversation = []
        
        with pytest.raises(GPTException):
            await self.summary_service.generate_summary(empty_session)
        
        print("✅ 错误处理测试完成！")

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理可能创建的临时文件
        pass


async def main():
    """主测试函数"""
    print("📊 开始总结服务测试...")
    print("=" * 60)
    
    # 创建总结服务实例
    summary_service = SummaryService()
    
    print(f"🔑 API密钥状态: {'已配置' if summary_service.api_key and summary_service.api_key != 'your_openai_api_key' else '未配置'}")
    print(f"📁 导出目录: {summary_service.export_dir}")
    print("-" * 60)
    
    # 检查API密钥有效性
    if summary_service.api_key and summary_service.api_key != 'your_openai_api_key':
        print("🔍 正在验证API密钥...")
        api_valid = await check_api_key(summary_service.api_key)
        if api_valid:
            print("✅ API密钥验证成功！")
        else:
            print("❌ API密钥验证失败！密钥可能无效或过期")
    
    # 询问用户是否使用真实API
    use_real_api = input("是否使用真实API进行测试？(y/n，默认n): ").lower().strip()
    use_real_api = use_real_api == 'y'
    
    if use_real_api:
        print("⚠️  将使用真实API进行测试...")
    else:
        print("🔧 将使用模拟数据进行测试...")
    
    # 创建测试会话
    test_session = Session()
    test_session.session_id = f"main_test_{uuid.uuid4().hex[:8]}"
    
    # 添加测试对话数据
    test_session.conversation = [
        {
            "transcript": "你好，我想学习英语。",
            "translation": "Hello, I want to learn English.",
            "source_lang": "zh-CN",
            "target_lang": "en-US",
            "timestamp": datetime.now().isoformat()
        },
        {
            "transcript": "That's great! English is a very useful language.",
            "translation": "太好了！英语是一门非常有用的语言。",
            "source_lang": "en-US",
            "target_lang": "zh-CN",
            "timestamp": datetime.now().isoformat()
        },
        {
            "transcript": "你能推荐一些学习方法吗？",
            "translation": "Can you recommend some learning methods?",
            "source_lang": "zh-CN",
            "target_lang": "en-US",
            "timestamp": datetime.now().isoformat()
        },
        {
            "transcript": "Sure! Reading, listening to music, and watching movies are great ways to learn.",
            "translation": "当然！阅读、听音乐和看电影都是学习的好方法。",
            "source_lang": "en-US",
            "target_lang": "zh-CN",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    print(f"📝 测试会话ID: {test_session.session_id}")
    print(f"💬 对话数量: {len(test_session.conversation)}")
    print("-" * 60)
    
    try:
        if use_real_api:
            # 使用真实API
            print("🔄 正在调用真实的OpenAI API生成总结...")
            result = await summary_service.generate_and_export_summary(
                session=test_session,
                filename=f"real_test_summary_{test_session.session_id}"
            )
        else:
            # 使用模拟数据
            print("🔄 正在使用模拟数据生成总结...")
            
            mock_summary = f"""# 英语学习会话总结

## 会话概览
- **会话ID**: {test_session.session_id}
- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **参与语言**: 中文(zh-CN) ↔ 英文(en-US)
- **主要话题**: 英语学习讨论

## 关键对话内容摘要
本次会话围绕英语学习展开，用户表达了学习英语的愿望，并寻求学习方法建议。对话展现了学习者的积极态度和对有效学习方法的渴望。

## 语言使用统计
- 中文消息: 2条
- 英文消息: 2条
- 总翻译次数: 4次

## 主要讨论话题
1. **学习意愿** - 用户表达学习英语的愿望
2. **语言价值** - 确认英语作为有用语言的地位
3. **学习方法** - 寻求和提供学习建议
4. **实用建议** - 推荐阅读、音乐、电影等学习方式

## 语言学习点
- 学习表达: "I want to learn English", "我想学习英语"
- 询问建议: "Can you recommend...?", "你能推荐...吗？"
- 积极回应: "That's great!", "太好了！"
- 学习方法词汇: "reading", "listening", "watching"

## 学习建议总结
对话中提到的学习方法：
- 📚 阅读 (Reading)
- 🎵 听音乐 (Listening to music)  
- 🎬 看电影 (Watching movies)

这是一个很好的英语学习启发对话，为初学者提供了实用的学习方向。"""

            with patch('httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "choices": [
                        {
                            "message": {
                                "content": mock_summary
                            }
                        }
                    ]
                }
                
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                result = await summary_service.generate_and_export_summary(
                    session=test_session,
                    filename=f"mock_test_summary_{test_session.session_id}"
                )
        
        print("✅ 总结生成成功！")
        print(f"📄 总结长度: {len(result['summary'])} 字符")
        print(f"📁 导出文件: {result['file_info']['filename']}")
        print(f"💾 文件大小: {result['file_info']['size']} bytes")
        print(f"🔗 文件路径: {result['file_info']['path']}")
        
        # 显示总结内容的前几行
        print("\n📋 总结内容预览:")
        print("-" * 40)
        summary_lines = result['summary'].split('\n')
        for i, line in enumerate(summary_lines[:10]):
            print(line)
            if i >= 9 and len(summary_lines) > 10:
                print("... (更多内容请查看导出文件)")
                break
        
        print("-" * 60)
        print("🎉 测试完成！")
        print("\n💡 提示:")
        print("   - 总结文件已保存到 exports/ 目录")
        print("   - 可以使用Markdown查看器打开文件")
        print("   - 支持自定义文件名和会话ID")
        
        return True
        
    except GPTException as e:
        print(f"❌ 总结服务错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


if __name__ == "__main__":
    # 运行主测试函数
    success = asyncio.run(main())
    
    if not success:
        print("\n❌ 测试失败！请检查错误信息。")
        exit(1) 