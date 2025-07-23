import os
import sys
import asyncio
import numpy as np
import wave
import io
from typing import Dict, Any

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from backend.services.asr_service import ASRService
from backend.utils.audio_utils import pcm_to_wav
from backend.utils.exceptions import ASRException

class TestASRService:
    """ASR服务测试类"""
    
    def __init__(self):
        """初始化测试类"""
        self.asr_service = ASRService()
        
    def generate_test_audio(self, duration: float = 2.0, frequency: float = 440.0, sample_rate: int = 16000) -> bytes:
        """
        生成测试音频数据（正弦波）
        
        Args:
            duration: 音频时长（秒）
            frequency: 频率（Hz）
            sample_rate: 采样率
            
        Returns:
            WAV格式的音频数据
        """
        try:
            # 生成正弦波
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            sine_wave = np.sin(2 * np.pi * frequency * t)
            
            # 转换为16位PCM
            pcm_data = (sine_wave * 32767).astype(np.int16)
            
            # 转换为WAV格式
            wav_data = pcm_to_wav(pcm_data, sample_rate)
            
            print(f"✅ 生成测试音频: {duration}秒, {frequency}Hz, 采样率{sample_rate}Hz")
            print(f"   音频数据大小: {len(wav_data)} 字节")
            
            return wav_data
            
        except Exception as e:
            print(f"❌ 生成测试音频失败: {str(e)}")
            raise
    
    def create_silence_audio(self, duration: float = 1.0, sample_rate: int = 16000) -> bytes:
        """
        创建静音音频
        
        Args:
            duration: 时长（秒）
            sample_rate: 采样率
            
        Returns:
            WAV格式的静音音频数据
        """
        try:
            # 生成静音数据
            silence = np.zeros(int(sample_rate * duration), dtype=np.int16)
            
            # 转换为WAV格式
            wav_data = pcm_to_wav(silence, sample_rate)
            
            print(f"✅ 生成静音音频: {duration}秒")
            return wav_data
            
        except Exception as e:
            print(f"❌ 生成静音音频失败: {str(e)}")
            raise
    
    def save_test_audio(self, audio_data: bytes, filename: str) -> str:
        """
        保存测试音频到文件
        
        Args:
            audio_data: 音频数据
            filename: 文件名
            
        Returns:
            保存的文件路径
        """
        try:
            filepath = os.path.join(os.path.dirname(__file__), filename)
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            print(f"✅ 音频已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ 保存音频文件失败: {str(e)}")
            raise
    
    async def test_wav_transcription(self):
        """测试WAV格式音频转录"""
        print("\n🔍 测试 WAV 格式音频转录...")
        
        try:
            # 生成测试音频
            test_audio = self.generate_test_audio(duration=3.0, frequency=440.0)
            
            # 保存测试音频文件
            audio_file = self.save_test_audio(test_audio, "test_wav_audio.wav")
            
            # 调用ASR服务
            result = await self.asr_service.transcribe(test_audio, format="wav")
            
            print(f"✅ WAV转录结果:")
            print(f"   文本: '{result.get('text', '')}'")
            print(f"   语言: {result.get('language', 'Unknown')}")
            print(f"   置信度: {result.get('confidence', 0.0)}")
            print(f"   是否最终结果: {result.get('is_final', False)}")
            
            return result
            
        except ASRException as e:
            print(f"❌ WAV转录失败 (ASR异常): {str(e)}")
            return None
        except Exception as e:
            print(f"❌ WAV转录失败 (其他异常): {str(e)}")
            return None
    
    async def test_pcm_transcription(self):
        """测试PCM格式音频转录"""
        print("\n🔍 测试 PCM 格式音频转录...")
        
        try:
            # 生成PCM测试数据
            duration = 2.0
            sample_rate = 16000
            frequency = 880.0  # A5音符
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            sine_wave = np.sin(2 * np.pi * frequency * t)
            pcm_data = (sine_wave * 32767).astype(np.int16)
            
            # 转换为字节数据
            pcm_bytes = pcm_data.tobytes()
            
            print(f"✅ 生成PCM数据: {len(pcm_data)} 样本, {len(pcm_bytes)} 字节")
            
            # 调用ASR服务
            result = await self.asr_service.transcribe(pcm_bytes, format="pcm")
            
            print(f"✅ PCM转录结果:")
            print(f"   文本: '{result.get('text', '')}'")
            print(f"   语言: {result.get('language', 'Unknown')}")
            print(f"   置信度: {result.get('confidence', 0.0)}")
            
            return result
            
        except ASRException as e:
            print(f"❌ PCM转录失败 (ASR异常): {str(e)}")
            return None
        except Exception as e:
            print(f"❌ PCM转录失败 (其他异常): {str(e)}")
            return None
    
    async def test_silence_transcription(self):
        """测试静音音频转录"""
        print("\n🔍 测试静音音频转录...")
        
        try:
            # 生成静音音频
            silence_audio = self.create_silence_audio(duration=2.0)
            
            # 调用ASR服务
            result = await self.asr_service.transcribe(silence_audio, format="wav")
            
            print(f"✅ 静音转录结果:")
            print(f"   文本: '{result.get('text', '')}'")
            print(f"   语言: {result.get('language', 'Unknown')}")
            print(f"   置信度: {result.get('confidence', 0.0)}")
            
            return result
            
        except ASRException as e:
            print(f"❌ 静音转录失败 (ASR异常): {str(e)}")
            return None
        except Exception as e:
            print(f"❌ 静音转录失败 (其他异常): {str(e)}")
            return None
    
    async def test_error_handling(self):
        """测试错误处理"""
        print("\n🔍 测试错误处理...")
        
        try:
            # 测试空数据
            print("   测试空音频数据...")
            try:
                result = await self.asr_service.transcribe(b"", format="wav")
                print(f"   意外成功: {result}")
            except ASRException as e:
                print(f"   ✅ 正确捕获空数据异常: {str(e)}")
            
            # 测试无效格式
            print("   测试无效音频格式...")
            try:
                result = await self.asr_service.transcribe(b"invalid_data", format="invalid")
                print(f"   意外成功: {result}")
            except ASRException as e:
                print(f"   ✅ 正确捕获无效格式异常: {str(e)}")
            
            # 测试损坏的音频数据
            print("   测试损坏的音频数据...")
            try:
                result = await self.asr_service.transcribe(b"not_audio_data", format="wav")
                print(f"   意外成功: {result}")
            except ASRException as e:
                print(f"   ✅ 正确捕获损坏数据异常: {str(e)}")
                
        except Exception as e:
            print(f"❌ 错误处理测试失败: {str(e)}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🎵 开始 ASR 服务测试")
        print("=" * 60)
        
        # 检查API密钥
        if not self.asr_service.api_key:
            print("❌ 错误: 未设置 OPENAI_API_KEY 环境变量")
            print("   请设置您的 OpenAI API 密钥后重试")
            return
        
        print(f"✅ API密钥已设置: {self.asr_service.api_key[:10]}...")
        print(f"✅ 使用模型: {self.asr_service.model}")
        print(f"✅ API端点: {self.asr_service.api_url}")
        
        # 运行各项测试
        test_results = {}
        
        # 测试WAV转录
        test_results['wav'] = await self.test_wav_transcription()
        
        # 测试PCM转录
        test_results['pcm'] = await self.test_pcm_transcription()
        
        # 测试静音转录
        test_results['silence'] = await self.test_silence_transcription()
        
        # 测试错误处理
        await self.test_error_handling()
        
        # 总结测试结果
        print("\n" + "=" * 60)
        print("📊 测试结果总结:")
        
        success_count = 0
        total_count = 0
        
        for test_name, result in test_results.items():
            total_count += 1
            if result is not None:
                success_count += 1
                print(f"   ✅ {test_name.upper()} 测试: 成功")
            else:
                print(f"   ❌ {test_name.upper()} 测试: 失败")
        
        print(f"\n🎯 测试完成: {success_count}/{total_count} 个测试通过")
        
        if success_count == total_count:
            print("🎉 所有测试都通过了！ASR服务工作正常。")
        else:
            print("⚠️  部分测试失败，请检查配置和网络连接。")
        
        return test_results

async def main():
    """主函数"""
    try:
        # 创建测试实例
        test_asr = TestASRService()
        
        # 运行所有测试
        results = await test_asr.run_all_tests()
        
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