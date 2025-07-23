import os
import sys
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from backend.services.translation_service import TranslationService
from backend.utils.sessions import Session
from backend.utils.exceptions import TranslationException

class TestTranslationService:
    """翻译服务测试类"""
    
    def __init__(self):
        """初始化测试类"""
        self.translation_service = TranslationService()
        self.test_session = Session("test_translation_session")
    
    def setup_test_session(self):
        """设置测试会话"""
        # 清空会话状态
        self.test_session.session_langs = []
        self.test_session.detected_lang = ''
        self.test_session.target_lang = ''
        self.test_session.conversation = []
        print(f"✅ 重置测试会话: {self.test_session.session_id}")
    
    async def test_basic_translation(self):
        """测试基本翻译功能"""
        print("\n🔍 测试基本翻译功能...")
        
        try:
            self.setup_test_session()
            
            # 模拟OpenAI API响应
            mock_response = {
                "choices": [{
                    "message": {
                        "content": "Hello, how are you?"
                    }
                }]
            }
            
            with patch('httpx.AsyncClient') as mock_client:
                # 设置mock响应
                mock_response_obj = MagicMock()
                mock_response_obj.status_code = 200
                mock_response_obj.json.return_value = mock_response
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response_obj
                )
                
                # 执行翻译
                result = await self.translation_service.translate(
                    session=self.test_session,
                    text="你好，你好吗？",
                    detect_language="chinese"
                )
                
                # 验证结果
                assert result["source_text"] == "你好，你好吗？"
                assert result["target_text"] == "Hello, how are you?"
                assert result["source_language"] is not None
                assert result["target_language"] is not None
                assert result["confidence"] >= 0.0
                
                print(f"   ✅ 翻译成功:")
                print(f"      原文: {result['source_text']}")
                print(f"      译文: {result['target_text']}")
                print(f"      源语言: {result['source_language']}")
                print(f"      目标语言: {result['target_language']}")
                print(f"      置信度: {result['confidence']}")
                
                return True
                
        except Exception as e:
            print(f"❌ 基本翻译测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_translation_with_session_update(self):
        """测试翻译过程中的会话更新"""
        print("\n🔍 测试翻译过程中的会话更新...")
        
        try:
            self.setup_test_session()
            
            # 模拟OpenAI API响应
            mock_response = {
                "choices": [{
                    "message": {
                        "content": "Good morning!"
                    }
                }]
            }
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_response_obj = MagicMock()
                mock_response_obj.status_code = 200
                mock_response_obj.json.return_value = mock_response
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response_obj
                )
                
                # 执行翻译
                await self.translation_service.translate(
                    session=self.test_session,
                    text="早上好！",
                    detect_language="chinese"
                )
                
                # 验证会话状态更新
                print(f"   检测到的语言: {self.test_session.detected_lang}")
                print(f"   目标语言: {self.test_session.target_lang}")
                print(f"   会话语言列表: {self.test_session.session_langs}")
                
                # 验证语言检测更新
                assert self.test_session.detected_lang != ''
                assert len(self.test_session.session_langs) > 0
                
                print("   ✅ 会话状态更新成功")
                return True
                
        except Exception as e:
            print(f"❌ 会话更新测试失败: {str(e)}")
            return False
    
    async def test_translate_and_save(self):
        """测试翻译并保存功能"""
        print("\n🔍 测试翻译并保存功能...")
        
        try:
            self.setup_test_session()
            
            # 模拟OpenAI API响应
            mock_response = {
                "choices": [{
                    "message": {
                        "content": "Thank you very much!"
                    }
                }]
            }
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_response_obj = MagicMock()
                mock_response_obj.status_code = 200
                mock_response_obj.json.return_value = mock_response
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response_obj
                )
                
                # 执行翻译并保存
                result = await self.translation_service.translate_and_save(
                    session=self.test_session,
                    text="非常感谢！",
                    detected_lang="chinese"
                )
                
                # 验证翻译结果
                assert result["source_text"] == "非常感谢！"
                assert result["target_text"] == "Thank you very much!"
                
                # 验证会话对话历史
                assert len(self.test_session.conversation) == 1
                conversation = self.test_session.conversation[0]
                assert conversation["transcript"] == "非常感谢！"
                assert conversation["translation"] == "Thank you very much!"
                assert conversation["source_lang"] is not None
                assert conversation["target_lang"] is not None
                
                print(f"   ✅ 翻译并保存成功:")
                print(f"      对话历史条数: {len(self.test_session.conversation)}")
                print(f"      最新对话: {conversation}")
                
                return True
                
        except Exception as e:
            print(f"❌ 翻译并保存测试失败: {str(e)}")
            return False
    
    async def test_multiple_translations(self):
        """测试多次翻译的会话管理"""
        print("\n🔍 测试多次翻译的会话管理...")
        
        try:
            self.setup_test_session()
            
            # 测试数据
            test_cases = [
                {"text": "你好", "response": "Hello"},
                {"text": "谢谢", "response": "Thank you"},
                {"text": "再见", "response": "Goodbye"}
            ]
            
            with patch('httpx.AsyncClient') as mock_client:
                for i, case in enumerate(test_cases):
                    mock_response = {
                        "choices": [{
                            "message": {
                                "content": case["response"]
                            }
                        }]
                    }
                    
                    mock_response_obj = MagicMock()
                    mock_response_obj.status_code = 200
                    mock_response_obj.json.return_value = mock_response
                    
                    mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                        return_value=mock_response_obj
                    )
                    
                    # 执行翻译并保存
                    await self.translation_service.translate_and_save(
                        session=self.test_session,
                        text=case["text"],
                        detected_lang="chinese"
                    )
                    
                    print(f"   第{i+1}次翻译: {case['text']} -> {case['response']}")
                
                # 验证会话状态
                assert len(self.test_session.conversation) == len(test_cases)
                print(f"   ✅ 多次翻译成功，共{len(self.test_session.conversation)}条对话记录")
                
                # 打印会话历史
                print("   📝 完整对话历史:")
                for i, conv in enumerate(self.test_session.conversation):
                    print(f"      {i+1}. {conv['transcript']} -> {conv['translation']}")
                
                return True
                
        except Exception as e:
            print(f"❌ 多次翻译测试失败: {str(e)}")
            return False
    
    async def test_api_error_handling(self):
        """测试API错误处理"""
        print("\n🔍 测试API错误处理...")
        
        try:
            self.setup_test_session()
            
            with patch('httpx.AsyncClient') as mock_client:
                # 模拟API错误
                mock_response_obj = MagicMock()
                mock_response_obj.status_code = 429  # Rate limit
                mock_response_obj.text = "Rate limit exceeded"
                mock_response_obj.json.return_value = {
                    "error": {
                        "message": "Rate limit exceeded"
                    }
                }
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response_obj
                )
                
                # 执行翻译，应该抛出异常
                try:
                    await self.translation_service.translate(
                        session=self.test_session,
                        text="测试错误处理",
                        detect_language="chinese"
                    )
                    print("❌ 应该抛出异常但没有抛出")
                    return False
                except TranslationException as e:
                    print(f"   ✅ 正确捕获API错误: {str(e)}")
                    return True
                
        except Exception as e:
            print(f"❌ 错误处理测试失败: {str(e)}")
            return False
    
    async def test_json_response_parsing(self):
        """测试JSON响应解析"""
        print("\n🔍 测试JSON响应解析...")
        
        try:
            self.setup_test_session()
            
            # 测试JSON格式响应
            json_response = {
                "translation": "Hello World",
                "confidence": 0.98
            }
            
            mock_response = {
                "choices": [{
                    "message": {
                        "content": json.dumps(json_response)
                    }
                }]
            }
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_response_obj = MagicMock()
                mock_response_obj.status_code = 200
                mock_response_obj.json.return_value = mock_response
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response_obj
                )
                
                result = await self.translation_service.translate(
                    session=self.test_session,
                    text="你好世界",
                    detect_language="chinese"
                )
                
                # 验证JSON解析
                assert result["target_text"] == "Hello World"
                assert result["confidence"] == 0.98
                
                print(f"   ✅ JSON响应解析成功:")
                print(f"      翻译结果: {result['target_text']}")
                print(f"      置信度: {result['confidence']}")
                
                return True
                
        except Exception as e:
            print(f"❌ JSON响应解析测试失败: {str(e)}")
            return False
    
    async def test_session_isolation(self):
        """测试会话隔离"""
        print("\n🔍 测试会话隔离...")
        
        try:
            # 创建两个不同的会话
            session1 = Session("session_1")
            session2 = Session("session_2")
            
            # 模拟OpenAI API响应
            mock_response = {
                "choices": [{
                    "message": {
                        "content": "Hello"
                    }
                }]
            }
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_response_obj = MagicMock()
                mock_response_obj.status_code = 200
                mock_response_obj.json.return_value = mock_response
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response_obj
                )
                
                # 在session1中翻译
                await self.translation_service.translate_and_save(
                    session=session1,
                    text="你好",
                    detected_lang="chinese"
                )
                
                # 在session2中翻译
                await self.translation_service.translate_and_save(
                    session=session2,
                    text="谢谢",
                    detected_lang="chinese"
                )
                
                # 验证会话隔离
                assert len(session1.conversation) == 1
                assert len(session2.conversation) == 1
                assert session1.conversation[0]["transcript"] == "你好"
                assert session2.conversation[0]["transcript"] == "谢谢"
                
                print(f"   ✅ 会话隔离成功:")
                print(f"      Session1对话数: {len(session1.conversation)}")
                print(f"      Session2对话数: {len(session2.conversation)}")
                print(f"      Session1内容: {session1.conversation[0]['transcript']}")
                print(f"      Session2内容: {session2.conversation[0]['transcript']}")
                
                return True
                
        except Exception as e:
            print(f"❌ 会话隔离测试失败: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🌐 开始翻译服务测试")
        print("=" * 60)
        
        # 运行各项测试
        test_results = {}
        
        test_results['basic_translation'] = await self.test_basic_translation()
        test_results['session_update'] = await self.test_translation_with_session_update()
        test_results['translate_and_save'] = await self.test_translate_and_save()
        test_results['multiple_translations'] = await self.test_multiple_translations()
        test_results['api_error_handling'] = await self.test_api_error_handling()
        test_results['json_parsing'] = await self.test_json_response_parsing()
        test_results['session_isolation'] = await self.test_session_isolation()
        
        # 总结测试结果
        print("\n" + "=" * 60)
        print("📊 测试结果总结:")
        
        success_count = 0
        total_count = 0
        
        for test_name, result in test_results.items():
            total_count += 1
            if result:
                success_count += 1
                print(f"   ✅ {test_name.replace('_', ' ').title()}: 成功")
            else:
                print(f"   ❌ {test_name.replace('_', ' ').title()}: 失败")
        
        print(f"\n🎯 测试完成: {success_count}/{total_count} 个测试通过")
        
        if success_count == total_count:
            print("🎉 所有测试都通过了！翻译服务工作正常。")
        else:
            print("⚠️  部分测试失败，请检查实现逻辑。")
        
        return test_results

async def main():
    """主函数"""
    try:
        # 创建测试实例
        test_manager = TestTranslationService()
        
        # 运行所有测试
        results = await test_manager.run_all_tests()
        
        return results
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试运行失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())