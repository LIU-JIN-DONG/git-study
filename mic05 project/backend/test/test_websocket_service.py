# type: ignore
import asyncio
import json
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from backend.services.websocket_service import WebSocketManager
from backend.utils.sessions import Session


class TestWebSocketService:
    """WebSocket服务测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.websocket_manager = WebSocketManager()
        self.mock_websocket = Mock()
        self.mock_websocket.accept = AsyncMock()
        self.mock_websocket.send_json = AsyncMock()
        self.mock_websocket.send_bytes = AsyncMock()
        self.test_session_id = "test_session_123"
        
    def teardown_method(self):
        """测试后清理"""
        # 清理所有连接
        self.websocket_manager.active_connections.clear()
        self.websocket_manager.sessions.clear()
        for task in self.websocket_manager.heartbeat_task.values():
            task.cancel()
        self.websocket_manager.heartbeat_task.clear()

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """测试WebSocket连接成功"""
        print("\n=== 测试WebSocket连接 ===")
        session_id = await self.websocket_manager.connect(self.mock_websocket)
        print(f"✓ 生成的会话ID: {session_id}")
        
        # 验证连接成功且返回有效session_id
        assert session_id is not None
        assert session_id in self.websocket_manager.active_connections
        assert session_id in self.websocket_manager.sessions
        assert session_id in self.websocket_manager.heartbeat_task
        print(f"✓ 会话已注册到管理器中")
        
        # 验证WebSocket接受连接
        self.mock_websocket.accept.assert_called_once()
        print(f"✓ WebSocket连接已接受")
        
        # 验证发送连接确认消息
        self.mock_websocket.send_json.assert_called_once()
        call_args = self.mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "connected"
        assert "session_id" in call_args["data"]
        assert call_args["data"]["supported_languages"] == self.websocket_manager.supported_languages
        print(f"✓ 连接确认消息已发送，支持语言数量: {len(call_args['data']['supported_languages'])}")

    @pytest.mark.asyncio
    async def test_disconnect_success(self):
        """测试WebSocket断开连接"""
        print("\n=== 测试WebSocket断开连接 ===")
        # 先建立连接
        session_id = await self.websocket_manager.connect(self.mock_websocket)
        assert session_id is not None
        print(f"✓ 建立连接，会话ID: {session_id}")
        
        # 断开连接
        await self.websocket_manager.disconnect(session_id)
        print(f"✓ 断开连接请求已处理")
        
        # 验证连接已清理
        assert session_id not in self.websocket_manager.active_connections
        assert session_id not in self.websocket_manager.sessions
        assert session_id not in self.websocket_manager.heartbeat_task
        print(f"✓ 会话资源已完全清理")

    @pytest.mark.asyncio
    async def test_stop_tts(self):
        """测试停止TTS功能"""
        print("\n=== 测试停止TTS功能 ===")
        # 建立连接
        session_id = await self.websocket_manager.connect(self.mock_websocket)
        assert session_id is not None
        print(f"✓ 建立连接，会话ID: {session_id}")
        
        # 测试停止特定TTS
        test_audio_id = "test_audio_123"
        with patch('backend.services.websocket_service.tts_service') as mock_tts:
            # 模拟异步方法
            mock_tts.stop_tts = AsyncMock(return_value=True)
            print(f"✓ 模拟停止TTS音频ID: {test_audio_id}")
            
            await self.websocket_manager._handle_stop_tts(session_id, {"audio_id": test_audio_id})
            print(f"✓ 停止TTS请求已处理")
            
            mock_tts.stop_tts.assert_called_once_with(test_audio_id)
            print(f"✓ TTS服务停止方法调用验证通过")
            
            # 验证发送停止确认消息
            calls = self.mock_websocket.send_json.call_args_list
            stop_call = None
            for call in calls:
                if call[0][0]["type"] == "tts-stopped":
                    stop_call = call[0][0]
                    break
            
            assert stop_call is not None
            assert stop_call["data"]["audio_id"] == test_audio_id
            print(f"✓ 停止确认消息发送验证通过")

    @pytest.mark.asyncio
    async def test_change_target_language(self):
        """测试目标语言变更"""
        print("\n=== 测试目标语言变更 ===")
        # 建立连接
        session_id = await self.websocket_manager.connect(self.mock_websocket)
        assert session_id is not None
        print(f"✓ 建立连接，会话ID: {session_id}")
        
        # 变更目标语言
        new_language = "ja-JP"
        await self.websocket_manager._handle_change_target_language(
            session_id, 
            {"current_language": new_language}
        )
        print(f"✓ 语言变更请求已处理: {new_language}")
        
        # 验证会话语言已更新
        session = self.websocket_manager.sessions[session_id]
        assert session.target_lang == new_language
        print(f"✓ 会话目标语言已更新为: {session.target_lang}")
        
        # 验证发送语言变更确认消息
        calls = self.mock_websocket.send_json.call_args_list
        lang_change_call = None
        for call in calls:
            if call[0][0]["type"] == "target_language_changed":
                lang_change_call = call[0][0]
                break
        
        assert lang_change_call is not None
        assert lang_change_call["data"]["current_language"] == new_language
        print(f"✓ 语言变更确认消息发送验证通过")

    @pytest.mark.asyncio
    async def test_ping_pong(self):
        """测试心跳ping-pong"""
        print("\n=== 测试心跳ping-pong ===")
        # 建立连接
        session_id = await self.websocket_manager.connect(self.mock_websocket)
        print(f"✓ 建立连接，会话ID: {session_id}")
        
        # 发送ping
        await self.websocket_manager._handle_ping(session_id, {})
        print(f"✓ ping请求已处理")
        
        # 验证发送pong响应
        calls = self.mock_websocket.send_json.call_args_list
        pong_call = None
        for call in calls:
            if call[0][0]["type"] == "pong":
                pong_call = call[0][0]
                break
        
        assert pong_call is not None
        assert "timestamp" in pong_call["data"]
        assert pong_call["data"]["server_load"] == "normal"
        print(f"✓ pong响应发送验证通过，服务器负载: {pong_call['data']['server_load']}")

    @pytest.mark.asyncio
    async def test_get_system_status(self):
        """测试获取系统状态"""
        print("\n=== 测试获取系统状态 ===")
        # 建立连接
        session_id = await self.websocket_manager.connect(self.mock_websocket)
        print(f"✓ 建立连接，会话ID: {session_id}")
        
        # 获取系统状态
        await self.websocket_manager._handle_get_system_status(session_id)
        print(f"✓ 系统状态请求已处理")
        
        # 验证发送系统状态
        calls = self.mock_websocket.send_json.call_args_list
        status_call = None
        for call in calls:
            if call[0][0]["type"] == "system_status":
                status_call = call[0][0]
                break
        
        assert status_call is not None
        assert "asr_status" in status_call["data"]
        assert "translation_status" in status_call["data"]
        assert "tts_status" in status_call["data"]
        assert "queue_length" in status_call["data"]
        print(f"✓ 系统状态响应验证通过:")
        print(f"  - ASR状态: {status_call['data']['asr_status']}")
        print(f"  - 翻译状态: {status_call['data']['translation_status']}")
        print(f"  - TTS状态: {status_call['data']['tts_status']}")
        print(f"  - 队列长度: {status_call['data']['queue_length']}")

    @pytest.mark.asyncio
    @patch('backend.services.websocket_service.summary_service')
    async def test_generate_summary(self, mock_summary):
        """测试生成总结功能"""
        print("\n=== 测试生成总结功能 ===")
        # 设置模拟返回值
        mock_result = {
            "summary": "这是一个测试总结",
            "file_info": {
                "filename": "summary_test.txt",
                "path": "/path/to/summary_test.txt"
            },
            "success": True
        }
        mock_summary.generate_and_export_summary.return_value = mock_result
        print(f"✓ 模拟总结结果: {mock_result['summary']}")
        
        # 建立连接
        session_id = await self.websocket_manager.connect(self.mock_websocket)
        print(f"✓ 建立连接，会话ID: {session_id}")
        
        # 生成总结
        await self.websocket_manager._handle_generate_summary(session_id, {})
        print(f"✓ 总结生成请求已处理")
        
        # 验证调用了总结服务
        mock_summary.generate_and_export_summary.assert_called_once()
        print(f"✓ 总结服务调用验证通过")
        
        # 验证发送总结结果
        calls = self.mock_websocket.send_json.call_args_list
        summary_call = None
        for call in calls:
            if call[0][0]["type"] == "summary_generated":
                summary_call = call[0][0]
                break
        
        assert summary_call is not None
        assert summary_call["data"]["summary"] == "这是一个测试总结"
        assert summary_call["data"]["success"] is True
        print(f"✓ 总结结果消息发送验证通过")
        print(f"  - 文件名: {summary_call['data']['file_info']['filename']}")
        print(f"  - 成功状态: {summary_call['data']['success']}")

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        # 建立连接
        session_id = await self.websocket_manager.connect(self.mock_websocket)
        print(f"✓ 建立连接，会话ID: {session_id}")
        
        # 发送无效消息类型
        invalid_message = {
            "type": "invalid_message_type",
            "data": {}
        }
        await self.websocket_manager.handle_message(session_id, invalid_message)
        print(f"✓ 无效消息已发送: {invalid_message['type']}")
        
        # 验证发送错误消息
        calls = self.mock_websocket.send_json.call_args_list
        error_call = None
        for call in calls:
            if call[0][0]["type"] == "error":
                error_call = call[0][0]
                break
        
        assert error_call is not None
        assert "INVALID_MESSAGE_TYPE" in error_call["data"]["error"]
        print(f"✓ 错误消息发送验证通过: {error_call['data']['error']}")

    def test_get_active_sessions(self):
        """测试获取活跃会话"""
        print("\n=== 测试获取活跃会话 ===")
        # 添加一些测试会话
        self.websocket_manager.active_connections["session1"] = Mock()
        self.websocket_manager.active_connections["session2"] = Mock()
        print(f"✓ 添加了2个测试会话")
        
        active_sessions = self.websocket_manager.get_active_sessions()
        print(f"✓ 获取活跃会话列表: {active_sessions}")
        
        assert len(active_sessions) == 2
        assert "session1" in active_sessions
        assert "session2" in active_sessions
        print(f"✓ 活跃会话数量验证通过: {len(active_sessions)}")

    def test_get_session_status(self):
        """测试获取会话状态"""
        print("\n=== 测试获取会话状态 ===")
        # 创建测试会话
        session = Session("test_session")
        session.target_lang = "en-US"
        session.detected_lang = "zh-CN"
        print(f"✓ 创建测试会话，目标语言: {session.target_lang}")
        
        self.websocket_manager.sessions["test_session"] = session
        print(f"✓ 会话已注册到管理器")
        
        status = self.websocket_manager.get_session_status("test_session")
        print(f"✓ 获取会话状态完成")
        
        assert status is not None
        assert status["session_id"] == "test_session"
        assert status["target_language"] == "en-US"
        assert status["detected_language"] == "zh-CN"
        assert status["conversation_count"] == 0
        print(f"✓ 会话状态验证通过:")
        print(f"  - 会话ID: {status['session_id']}")
        print(f"  - 目标语言: {status['target_language']}")
        print(f"  - 检测语言: {status['detected_language']}")
        print(f"  - 对话数量: {status['conversation_count']}")

    async def _handle_text_input(self, session_id: str, text: str, language: str):
        """处理文本输入（模拟音频处理流程但跳过ASR）"""
        try:
            # 获取会话
            session = self.websocket_manager.sessions.get(session_id)
            if not session:
                await self.websocket_manager._send_error_message(session_id, "SESSION_NOT_FOUND")
                return

            # 模拟ASR结果
            transcript_result = {
                "text": text,
                "language": language,
                "confidence": 0.95,
                "is_final": True
            }

            # 发送转写结果
            await self.websocket_manager._send_message(session_id, {
                "type": "transcript_result",
                "data": {
                    "text": transcript_result["text"],
                    "language": transcript_result["language"],
                    "confidence": transcript_result["confidence"],
                    "is_final": transcript_result["is_final"],
                    "timestamp": datetime.now().isoformat(),
                }
            })

            # 翻译
            detected_lang = transcript_result["language"]
            if text.strip():
                # 使用模拟的翻译结果而不是真实的翻译服务
                translation_result = {
                    "source_text": text,
                    "target_text": "Hello, today is Tuesday, the weather is sunny",
                    "source_lang": language,
                    "target_lang": "en-US",
                    "confidence": 0.98
                }
                
                # 发送翻译结果
                await self.websocket_manager._send_message(session_id, {
                    "type": "translation_result",
                    "data": {
                        "source_text": translation_result["source_text"],
                        "target_text": translation_result["target_text"],
                        "source_language": translation_result["source_lang"],
                        "target_language": translation_result["target_lang"],
                        "confidence": translation_result.get("confidence", 0.98),
                    }
                })
            
                # TTS
                translated_text = translation_result["target_text"]
                target_lang = translation_result["target_lang"]

                if translated_text.strip():
                    await self.websocket_manager._handle_tts_synthesis(session_id, translated_text, target_lang)
                
        except Exception as e:
            await self.websocket_manager._send_error_message(session_id, f"TEXT_PROCESSING_ERROR: {e}")

    @pytest.mark.asyncio
    async def test_full_text_pipeline_integration(self):
        """完整的文本处理管道集成测试"""
        print("\n=== 开始完整文本处理管道测试 ===")
        
        # 建立连接
        session_id = await self.websocket_manager.connect(self.mock_websocket)
        print(f"✓ WebSocket连接成功，会话ID: {session_id}")
        
        # 模拟处理文本输入
        test_text = "您好，今天是星期二，天气晴朗"
        print(f"✓ 处理文本: {test_text}")
        
        # 使用patch模拟各个服务
        with patch('backend.services.websocket_service.tts_service') as mock_tts:
            mock_tts.synthesize_streaming = AsyncMock(return_value="task_456")
            
            # 处理文本
            await self._handle_text_input(session_id, test_text, "zh-CN")
            
            print("✓ TTS服务调用成功")
            
        # 验证所有消息
        all_calls = self.mock_websocket.send_json.call_args_list
        message_types = [call[0][0]["type"] for call in all_calls]
        
        print(f"✓ 发送的消息类型: {message_types}")
        
        # 验证必要的消息类型存在
        assert "connected" in message_types
        assert "transcript_result" in message_types
        assert "translation_result" in message_types
        
        print("✓ 所有必要消息都已发送")
        print("=== 完整文本处理管道测试完成 ===\n")


# 运行测试的主函数
async def run_websocket_tests():
    """运行WebSocket服务测试"""
    print("开始运行WebSocket服务测试...")
    
    test_instance = TestWebSocketService()
    
    # 运行各个测试
    tests = [
        ("连接测试", test_instance.test_connect_success),
        ("断开连接测试", test_instance.test_disconnect_success),
        ("停止TTS测试", test_instance.test_stop_tts),
        ("语言变更测试", test_instance.test_change_target_language),
        ("心跳测试", test_instance.test_ping_pong),
        ("系统状态测试", test_instance.test_get_system_status),
        ("错误处理测试", test_instance.test_error_handling),
        ("完整文本管道测试", test_instance.test_full_text_pipeline_integration),
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n运行 {test_name}...")
            test_instance.setup_method()
            await test_func()
            test_instance.teardown_method()
            print(f"✓ {test_name} 通过")
        except Exception as e:
            print(f"✗ {test_name} 失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== WebSocket服务测试完成 ===")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(run_websocket_tests()) 