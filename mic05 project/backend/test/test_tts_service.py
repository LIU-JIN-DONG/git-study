import asyncio
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import uuid
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.tts_service import TTSService, tts_service
from backend.utils.exceptions import TTSException
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


class TestTTSService:
    """TTS服务测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.tts = TTSService()
        self.test_text = "你好，今天是星期一，天气好热，有没有什么方法可以快速降温"
        self.test_language = "zh-CN"
        
        # 确保test文件夹存在
        self.test_dir = Path("backend/test")
        self.test_dir.mkdir(exist_ok=True)

    @pytest.mark.asyncio
    async def test_synthesize_and_save_mp3(self):
        """测试文本转语音并保存MP3文件"""
        # 模拟API响应 - 创建一个简单的MP3文件头
        mock_mp3_data = b'\xff\xfb\x90\x00' + b'\x00' * 1000  # 模拟MP3数据
        
        with patch('httpx.AsyncClient') as mock_client:
            # 设置模拟响应
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = mock_mp3_data
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # 执行TTS合成
            result = await self.tts.synthesize(
                text=self.test_text,
                language=self.test_language,
                output_format="mp3"
            )
            
            # 验证结果
            assert result["format"] == "mp3"
            assert result["language"] == self.test_language
            assert result["text"] == self.test_text
            assert result["voice"] == "alloy"  # 中文对应的声音
            assert result["audio_data"] == mock_mp3_data
            
            # 保存MP3文件
            output_file = self.test_dir / f"test_tts_{uuid.uuid4().hex[:8]}.mp3"
            with open(output_file, "wb") as f:
                f.write(result["audio_data"])
            
            # 验证文件是否创建成功
            assert output_file.exists()
            assert output_file.stat().st_size > 0
            
            print(f"✅ TTS测试完成！MP3文件已保存到: {output_file}")

    @pytest.mark.asyncio
    async def test_synthesize_with_real_api(self):
        """使用真实API测试TTS（需要有效的API密钥）"""
        # 这个测试只在有API密钥时运行
        if not self.tts.api_key or self.tts.api_key == "your_openai_api_key":
            pytest.skip("需要有效的OpenAI API密钥")
        
        try:
            # 执行真实的TTS合成
            result = await self.tts.synthesize(
                text=self.test_text,
                language=self.test_language,
                output_format="mp3"
            )
            
            # 验证结果
            assert result["format"] == "mp3"
            assert result["language"] == self.test_language
            assert result["text"] == self.test_text
            assert len(result["audio_data"]) > 0
            
            # 保存真实的MP3文件
            output_file = self.test_dir / "real_tts_test.mp3"
            with open(output_file, "wb") as f:
                f.write(result["audio_data"])
            
            print(f"✅ 真实API测试完成！MP3文件已保存到: {output_file}")
            
        except Exception as e:
            pytest.fail(f"真实API测试失败: {str(e)}")

    @pytest.mark.asyncio
    async def test_voice_mapping(self):
        """测试不同语言的声音映射"""
        test_cases = [
            ("zh-CN", "alloy"),
            ("en-US", "shimmer"),
            ("ja-JP", "nova"),
            ("ko-KR", "echo"),
            ("fr-FR", "fable"),
        ]
        
        mock_mp3_data = b'\xff\xfb\x90\x00' + b'\x00' * 500
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = mock_mp3_data
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            for language, expected_voice in test_cases:
                result = await self.tts.synthesize(
                    text="Hello world",
                    language=language,
                    output_format="mp3"
                )
                
                assert result["voice"] == expected_voice
                print(f"✅ {language} -> {expected_voice}")

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        with patch('httpx.AsyncClient') as mock_client:
            # 模拟API错误
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "API Error"
            mock_response.json.return_value = {"error": {"message": "Invalid request"}}
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # 测试是否正确抛出异常
            with pytest.raises(TTSException):
                await self.tts.synthesize(
                    text=self.test_text,
                    language=self.test_language
                )

    def test_get_supported_voices(self):
        """测试获取支持的声音映射"""
        voices = self.tts.get_supported_voices()
        
        assert isinstance(voices, dict)
        assert "zh-CN" in voices
        assert voices["zh-CN"] == "alloy"
        assert "en-US" in voices
        assert voices["en-US"] == "shimmer"

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理可能创建的临时文件
        pass


# 独立的测试函数，用于快速测试
async def quick_tts_test():
    """快速TTS测试函数"""
    print("🎵 开始TTS测试...")
    
    tts = TTSService()
    test_text = "你好，今天是星期一，天气好热，有没有什么方法可以快速降温"
    
    # 模拟API响应
    mock_mp3_data = b'\xff\xfb\x90\x00' + b'\x00' * 2000  # 模拟更大的MP3数据
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = mock_mp3_data
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # 执行TTS合成
        result = await tts.synthesize(
            text=test_text,
            language="zh-CN",
            output_format="mp3"
        )
        
        # 保存MP3文件
        test_dir = Path("backend/test")
        test_dir.mkdir(exist_ok=True)
        
        output_file = test_dir / "quick_test_output.mp3"
        with open(output_file, "wb") as f:
            f.write(result["audio_data"])
        
        print(f"✅ 快速测试完成！")
        print(f"📄 输入文本: {test_text}")
        print(f"🎤 使用声音: {result['voice']}")
        print(f"💾 文件保存到: {output_file}")
        print(f"📊 文件大小: {len(result['audio_data'])} bytes")


async def main():
    """主测试函数"""
    print("🎵 开始TTS服务测试...")
    print("=" * 60)
    
    # 创建TTS服务实例
    tts = TTSService()
    
    # 测试文本
    test_text = "你好，今天是星期一，天气好热，有没有什么方法可以快速降温"
    
    print(f"📝 测试文本: {test_text}")
    print(f"🌐 目标语言: zh-CN")
    print(f"🎤 使用声音: {tts.voice_mapping.get('zh-CN', 'alloy')}")
    print(f"🔑 API密钥状态: {'已配置' if tts.api_key and tts.api_key != 'your_openai_api_key' else '未配置'}")
    print("-" * 60)
    
    # 检查API密钥有效性
    if tts.api_key and tts.api_key != 'your_openai_api_key':
        print("🔍 正在验证API密钥...")
        api_valid = await check_api_key(tts.api_key)
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
    
    try:
        if use_real_api:
            # 使用真实API
            print("🔄 正在调用真实的OpenAI TTS API...")
            result = await tts.synthesize(
                text=test_text,
                language="zh-CN",
                output_format="mp3"
            )
        else:
            # 使用模拟数据
            print("🔄 正在进行TTS合成（使用模拟数据）...")
            
            # 创建模拟的MP3数据
            mock_mp3_data = b'\xff\xfb\x90\x00' + b'\x00' * 3000  # 模拟MP3数据
            
            # 使用模拟数据而不是真实API
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.content = mock_mp3_data
                
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                result = await tts.synthesize(
                    text=test_text,
                    language="zh-CN",
                    output_format="mp3"
                )
        
        # 创建输出目录
        output_dir = Path("backend/test")
        output_dir.mkdir(exist_ok=True)
        
        # 保存MP3文件
        output_file = output_dir / "tts_test_output.mp3"
        with open(output_file, "wb") as f:
            f.write(result["audio_data"])
        
        print("✅ TTS合成成功！")
        print(f"📁 文件保存位置: {output_file.absolute()}")
        print(f"📊 文件大小: {len(result['audio_data'])} bytes")
        print(f"🎯 任务ID: {result['task_id']}")
        print(f"🔊 使用声音: {result['voice']}")
        
        # 验证文件
        if output_file.exists() and output_file.stat().st_size > 0:
            print("✅ MP3文件创建成功！")
            print(f"💾 实际文件大小: {output_file.stat().st_size} bytes")
        else:
            print("❌ MP3文件创建失败！")
            
    except TTSException as e:
        print(f"❌ TTS服务错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False
    
    print("=" * 60)
    print("🎉 测试完成！")
    print("\n💡 提示:")
    print("   - 如果您有有效的OpenAI API密钥，将生成真实的MP3文件")
    print("   - 如果没有API密钥，将使用模拟数据进行测试")
    print("   - 生成的MP3文件保存在 backend/test/ 目录下")
    return True


if __name__ == "__main__":
    # 运行主测试函数
    success = asyncio.run(main())
    
    if not success:
        print("\n❌ 测试失败！请检查错误信息。")
        exit(1) 