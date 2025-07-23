#!/usr/bin/env python3
"""
测试音频转换功能
"""
import os
import sys
import base64

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.audio_utils import base64_to_wav, AudioConverter
from utils.exceptions import AudioProcessingException

def test_adpcm_conversion():
    """测试ADPCM转换功能"""
    print("=== 测试ADPCM转换功能 ===")
    
    # 创建一个简单的ADPCM测试数据
    # 这里使用adpcm_converter.py中的示例数据
    dummy_header = b'\x00\x00\x00\x14'  # predict=0, index=0, 负载长度=20字节
    dummy_payload = b'\xff\xee\xdd\xcc\xbb\xaa\x99\x88\x77\x66\x55\x44\x33\x22\x11\x00\x11\x22\x33\x44'
    test_adpcm_data = dummy_header + dummy_payload
    
    # 转换为base64
    base64_adpcm = base64.b64encode(test_adpcm_data).decode('ascii')
    
    try:
        # 测试base64_adpcm转换
        wav_data = base64_to_wav(base64_adpcm, format="base64_adpcm", sample_rate=16000)
        
        print(f"转换成功!")
        print(f"原始ADPCM数据大小: {len(test_adpcm_data)} bytes")
        print(f"Base64编码长度: {len(base64_adpcm)} 字符")
        print(f"生成的WAV数据大小: {len(wav_data)} bytes")
            
        # 检查WAV文件头
        if wav_data[:4] == b'RIFF' and wav_data[8:12] == b'WAVE':
            print("✓ 生成的WAV文件头格式正确")
        else:
            print("✗ WAV文件头格式不正确")
        
        return True
        
    except Exception as e:
        print(f"转换失败: {e}")
        return False

def test_real_bluetooth_microphone_data():
    """测试真实的蓝牙麦克风Base64 ADPCM数据"""
    print("\n=== 测试真实蓝牙麦克风数据 ===")
            
    # 读取真实的蓝牙麦克风数据
    bluetooth_data_file = os.path.join(os.path.dirname(__file__), 'bluetooth_microphone_base64.txt')
    
    try:
        with open(bluetooth_data_file, 'r') as f:
            base64_adpcm_data = f.read().strip()
        
        print(f"读取Base64数据长度: {len(base64_adpcm_data)} 字符")
            
        # 解码base64数据查看原始数据长度
        try:
            decoded_data = base64.b64decode(base64_adpcm_data)
            print(f"解码后ADPCM数据大小: {len(decoded_data)} bytes")
        except Exception as e:
            print(f"Base64解码失败: {e}")
            return False
        
        # 测试base64_adpcm转换
        wav_data = base64_to_wav(base64_adpcm_data, format="base64_adpcm", sample_rate=16000)
        
        print(f"转换成功!")
        print(f"生成的WAV数据大小: {len(wav_data)} bytes")
        
        # 检查WAV文件头
        if wav_data[:4] == b'RIFF' and wav_data[8:12] == b'WAVE':
            print("✓ 生成的WAV文件头格式正确")
        else:
            print("✗ WAV文件头格式不正确")
        
        # 计算预估的音频时长
        # WAV文件头通常在44字节左右，剩余数据是PCM数据
        pcm_data_size = len(wav_data) - 44  # 大概的PCM数据大小
        sample_count = pcm_data_size // 2  # 16位PCM，每个样本2字节
        duration = sample_count / 16000  # 采样率16000Hz
        print(f"预估音频时长: {duration:.2f} 秒")
        
        return True
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 {bluetooth_data_file}")
        return False
    except Exception as e:
        print(f"转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_converter_class():
    """测试AudioConverter类的功能"""
    print("\n=== 测试AudioConverter类 ===")
    
    converter = AudioConverter()
    
    # 创建测试ADPCM数据
    dummy_header = b'\x00\x00\x00\x10'  # predict=0, index=0, 负载长度=16字节
    dummy_payload = b'\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff\x00'
    test_adpcm_data = dummy_header + dummy_payload
    
    try:
        # 测试ADPCM到PCM转换
        pcm_data = converter.adpcm_to_pcm(test_adpcm_data)
        print(f"ADPCM到PCM转换成功!")
        print(f"PCM样本数: {len(pcm_data)}")
        print(f"PCM数据类型: {pcm_data.dtype}")
        
        # 测试PCM到WAV转换
        wav_data = converter.pcm_to_wav(pcm_data, sample_rate=16000)
        print(f"PCM到WAV转换成功!")
        print(f"WAV数据大小: {len(wav_data)} bytes")
        
        # 检查WAV文件头
        if wav_data[:4] == b'RIFF' and wav_data[8:12] == b'WAVE':
            print("✓ 生成的WAV文件头格式正确")
        else:
            print("✗ WAV文件头格式不正确")
        
        return True
        
    except Exception as e:
        print(f"转换失败: {e}")
        return False

def test_base64_wav_format():
    """测试base64_wav格式处理"""
    print("\n=== 测试base64_wav格式处理 ===")
    
    # 创建一个最小的WAV文件数据
    wav_header = b'RIFF\x24\x00\x00\x00WAVE'
    wav_data = wav_header + b'\x00' * 24  # 简单的WAV数据
    
    # 转换为base64
    base64_wav = base64.b64encode(wav_data).decode('ascii')
    
    try:
        # 测试base64_wav转换
        result_wav = base64_to_wav(base64_wav, format="base64_wav")
        
        print(f"base64_wav转换成功!")
        print(f"原始WAV数据大小: {len(wav_data)} bytes")
        print(f"结果WAV数据大小: {len(result_wav)} bytes")
        
        # 验证数据一致性
        if result_wav == wav_data:
            print("✓ 数据一致性验证通过")
        else:
            print("✗ 数据一致性验证失败")
        
        return True
        
    except Exception as e:
        print(f"转换失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试音频转换功能...")
    
    # 运行所有测试
    tests = [
        test_adpcm_conversion,
        test_real_bluetooth_microphone_data,  # 新增的真实数据测试
        test_audio_converter_class,
        test_base64_wav_format
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"测试出错: {e}")
            results.append(False)
    
    # 输出测试结果
    print(f"\n=== 测试结果 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过!")
    else:
        print("✗ 部分测试失败!")

    print("\n注意: 测试过程中生成的WAV文件会保存在backend/test/目录中供进一步验证。")