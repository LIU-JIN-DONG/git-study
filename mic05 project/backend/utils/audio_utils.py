import tempfile
from typing import List,Union
import os
import struct
import io
import wave
import numpy as np
from pydub import AudioSegment
from utils.exceptions import AudioProcessingException
class AudioConverter:
    """音频格式转换工具类"""

    # ADPCM转换查找表
    ADPCM_INDEX_TABLE = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]

    ADPCM_STEP_TABLE = [
        7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45,
        50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307,
        337, 371, 408, 449, 494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066,
        2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
        15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767
    ]

    def __init__(self):
        self.last_packet_number=-1
        
    def adpcm_to_pcm(self,adpcm_data:bytes) -> np.ndarray:
        """
        将ADPCM数据转换为PCM数据
        
        Args:
            adpcm_data: ADPCM格式的字节数据
            
        Returns:
            PCM数据的numpy数组
        """
        try:
            pcm_samples = []
            data_len = len(adpcm_data)
            offset = 0
            
            while offset < data_len:
                # 确保有足够的数据读取头部
                if offset + 4 > data_len:
                    break
                
                # 读取ADPCM块头部
                predict = struct.unpack_from('<h', adpcm_data, offset)[0]  # 有符号16位整数
                predict_idx = adpcm_data[offset + 2]
                payload_byte_count = adpcm_data[offset + 3]
                sample_count = payload_byte_count * 2
                
                # 计算偏移量
                header_end_offset = offset + 4
                payload_end_offset = header_end_offset + payload_byte_count
                
                # 检查数据长度是否足够
                if payload_end_offset > data_len:
                    break
                
                # 提取ADPCM有效载荷
                adpcm_payload = adpcm_data[header_end_offset:payload_end_offset]
                
                # 解码ADPCM数据
                for i in range(sample_count):
                    # 获取4位代码
                    code = (adpcm_payload[i // 2] >> 4) if (i % 2 == 0) else (adpcm_payload[i // 2] & 0x0F)
                    
                    # 获取步长
                    step = self.ADPCM_STEP_TABLE[predict_idx]
                    
                    # 计算差值
                    diffq = step >> 3
                    if code & 4:
                        diffq += step
                    step >>= 1
                    if code & 2:
                        diffq += step
                    step >>= 1
                    if code & 1:
                        diffq += step
                    
                    # 更新预测值
                    if code & 8:
                        predict = predict - diffq
                    else:
                        predict = predict + diffq
                    
                    # 限制预测值范围
                    predict = max(-32768, min(32767, predict))
                    
                    # 更新索引
                    predict_idx += self.ADPCM_INDEX_TABLE[code]
                    predict_idx = max(0, min(88, predict_idx))
                    
                    # 添加PCM样本
                    pcm_samples.append(predict)
                
                # 移动到下一个块
                offset = payload_end_offset
            
            # 转换为numpy数组
            return np.array(pcm_samples, dtype=np.int16)
            
        except Exception as e:
            raise AudioProcessingException(f"ADPCM to PCM conversion failed: {str(e)}")
    
    def pcm_to_wav(self,pcm_data:np.ndarray,sample_rate:int=16000,channels:int=1) -> bytes:
        """
        将PCM数据转换为WAV格式
        
        Args:
            pcm_data: PCM数据的numpy数组
            sample_rate: 采样率，默认16000Hz
            channels: 声道数，默认1（单声道）
            
        Returns:
            WAV格式的字节数据
        """
        try:
            # 确保数据是16位整数
            if pcm_data.dtype != np.int16:
                pcm_data = pcm_data.astype(np.int16)
            
            # 创建内存中的WAV文件
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)  # 16位 = 2字节
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_data.tobytes())
            
            wav_buffer.seek(0)
            return wav_buffer.read()
            
        except Exception as e:
            raise AudioProcessingException(f"PCM to WAV conversion failed: {str(e)}")

    def mp3_to_pcm(self, mp3_data: bytes, target_sample_rate: int = 16000) -> np.ndarray:
        """
        将MP3数据转换为PCM数据
        
        Args:
            mp3_data: MP3格式的字节数据
            target_sample_rate: 目标采样率，默认16000Hz
            
        Returns:
            PCM数据的numpy数组
        """
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(mp3_data)
                temp_file_path = temp_file.name
            
            try:
                # 使用pydub加载MP3文件
                audio = AudioSegment.from_mp3(temp_file_path)
                
                # 转换为单声道
                if audio.channels > 1:
                    audio = audio.set_channels(1)
                
                # 重采样到目标采样率
                if audio.frame_rate != target_sample_rate:
                    audio = audio.set_frame_rate(target_sample_rate)
                
                # 转换为16位PCM
                audio = audio.set_sample_width(2)  # 16位 = 2字节
                
                # 获取原始PCM数据
                pcm_data = np.frombuffer(audio.raw_data, dtype=np.int16)
                
                return pcm_data
                
            finally:
                # 清理临时文件
                os.unlink(temp_file_path)
                
        except Exception as e:
            raise AudioProcessingException(f"MP3 to PCM conversion failed: {str(e)}")

    def pcm_to_adpcm(self, pcm_data: np.ndarray, chunk_size: int = 256) -> List[bytes]:
        """
        将PCM数据转换为ADPCM格式（分块处理）
        
        Args:
            pcm_data: PCM数据的numpy数组
            chunk_size: 每个ADPCM块的PCM样本数，默认256
            
        Returns:
            ADPCM数据块的列表
        """
        try:
            # 确保数据是16位整数
            if pcm_data.dtype != np.int16:
                pcm_data = pcm_data.astype(np.int16)
            
            adpcm_chunks = []
            pcm_index = 0
            
            while pcm_index < len(pcm_data):
                # 提取PCM块
                pcm_chunk = pcm_data[pcm_index:pcm_index + chunk_size]
                pcm_index += chunk_size
                
                # 如果块大小不足，补零
                if len(pcm_chunk) < chunk_size:
                    pcm_chunk = np.pad(pcm_chunk, (0, chunk_size - len(pcm_chunk)), 'constant')
                
                # 转换为ADPCM
                adpcm_chunk = self._pcm_chunk_to_adpcm(pcm_chunk)
                
                if adpcm_chunk:
                    adpcm_chunks.append(adpcm_chunk)
            
            return adpcm_chunks
            
        except Exception as e:
            raise AudioProcessingException(f"PCM to ADPCM conversion failed: {str(e)}")

    def _pcm_chunk_to_adpcm(self, pcm_chunk: np.ndarray) -> bytes:
        """
        将单个PCM块转换为ADPCM
        
        Args:
            pcm_chunk: PCM数据块
            
        Returns:
            ADPCM字节数据
        """
        try:
            # 简化的ADPCM编码实现
            # 这里实现基本的ADPCM编码逻辑
            
            # 初始化
            predict = 0
            predict_idx = 0
            
            # 创建ADPCM缓冲区
            adpcm_buffer = bytearray(len(pcm_chunk) // 2 + 4)
            
            # 设置包头 "ADP "
            adpcm_buffer[0] = ord('A')  # 65
            adpcm_buffer[1] = ord('D')  # 68
            adpcm_buffer[2] = ord('P')  # 80
            adpcm_buffer[3] = ord(' ')  # 32
            
            # 编码PCM数据
            # 这里需要实现完整的ADPCM编码算法
            # 为了简化，我们使用基本的差值编码
            
            encoded_data = []
            for i in range(0, len(pcm_chunk), 2):
                if i + 1 < len(pcm_chunk):
                    # 简化的编码逻辑
                    sample = pcm_chunk[i]
                    diff = sample - predict
                    
                    # 量化差值（简化实现）
                    code = 0
                    if abs(diff) > 1000:
                        code = 8 if diff < 0 else 0
                    
                    encoded_data.append(code)
                    predict = sample
            
            # 将编码数据添加到缓冲区
            for i, code in enumerate(encoded_data):
                if i + 4 < len(adpcm_buffer):
                    adpcm_buffer[i + 4] = code
            
            return bytes(adpcm_buffer)
            
        except Exception as e:
            raise AudioProcessingException(f"PCM chunk to ADPCM conversion failed: {str(e)}")
    
    def resample_pcm(self, pcm_data: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
        """
        重采样PCM数据
        
        Args:
            pcm_data: 原始PCM数据
            source_rate: 原始采样率
            target_rate: 目标采样率
            
        Returns:
            重采样后的PCM数据
        """
        try:
            if source_rate == target_rate:
                return pcm_data
            
            # 计算重采样比例
            ratio = target_rate / source_rate
            new_length = int(len(pcm_data) * ratio)
            
            # 简单的线性插值重采样
            resampled_data = np.zeros(new_length, dtype=np.int16)
            
            for i in range(new_length):
                old_index = int(i / ratio)
                if old_index < len(pcm_data):
                    resampled_data[i] = pcm_data[old_index]
            
            return resampled_data
            
        except Exception as e:
            raise AudioProcessingException(f"PCM resampling failed: {str(e)}")

    
# 全局转换器实例
audio_converter = AudioConverter()

# 便利函数
def adpcm_to_pcm(adpcm_data: bytes) -> np.ndarray:
    """ADPCM转PCM的便利函数"""
    return audio_converter.adpcm_to_pcm(adpcm_data)

def pcm_to_wav(pcm_data: np.ndarray, sample_rate: int = 16000) -> bytes:
    """PCM转WAV的便利函数"""
    return audio_converter.pcm_to_wav(pcm_data, sample_rate)

def mp3_to_pcm(mp3_data: bytes, target_sample_rate: int = 16000) -> np.ndarray:
    """MP3转PCM的便利函数"""
    return audio_converter.mp3_to_pcm(mp3_data, target_sample_rate)

def pcm_to_adpcm(pcm_data: np.ndarray, chunk_size: int = 256) -> List[bytes]:
    """PCM转ADPCM的便利函数"""
    return audio_converter.pcm_to_adpcm(pcm_data, chunk_size)

def process_audio_data(audio_data: bytes, source_format: str, target_format: str, 
                      sample_rate: int = 16000) -> Union[bytes, np.ndarray, List[bytes]]:
    """
    处理音频数据的通用函数
    
    Args:
        audio_data: 原始音频数据
        source_format: 源格式 ('adpcm', 'pcm', 'mp3', 'wav')
        target_format: 目标格式 ('adpcm', 'pcm', 'mp3', 'wav')
        sample_rate: 采样率
        
    Returns:
        转换后的音频数据
    """
    try:
        # 根据源格式转换为PCM
        if source_format.lower() == 'adpcm':
            pcm_data = adpcm_to_pcm(audio_data)
        elif source_format.lower() == 'mp3':
            pcm_data = mp3_to_pcm(audio_data, sample_rate)
        elif source_format.lower() == 'wav':
            # 从WAV文件提取PCM数据
            audio_segment = AudioSegment.from_wav(io.BytesIO(audio_data))
            pcm_data = np.frombuffer(audio_segment.raw_data, dtype=np.int16)
        elif source_format.lower() == 'pcm':
            pcm_data = np.frombuffer(audio_data, dtype=np.int16)
        else:
            raise AudioProcessingException(f"Unsupported source format: {source_format}")
        
        # 根据目标格式转换
        if target_format.lower() == 'pcm':
            return pcm_data
        elif target_format.lower() == 'wav':
            return pcm_to_wav(pcm_data, sample_rate)
        elif target_format.lower() == 'adpcm':
            return pcm_to_adpcm(pcm_data)
        elif target_format.lower() == 'mp3':
            # 先转换为WAV，再转换为MP3
            wav_data = pcm_to_wav(pcm_data, sample_rate)
            audio_segment = AudioSegment.from_wav(io.BytesIO(wav_data))
            mp3_buffer = io.BytesIO()
            audio_segment.export(mp3_buffer, format="mp3")
            mp3_buffer.seek(0)
            return mp3_buffer.read()
        else:
            raise AudioProcessingException(f"Unsupported target format: {target_format}")
            
    except Exception as e:
        raise AudioProcessingException(f"Audio processing failed: {str(e)}")

def process_audio_to_wav(audio_data: bytes, source_format: str, sample_rate: int = 16000) -> bytes:
    """
    将音频数据处理为WAV格式的辅助函数
    
    Args:
        audio_data: 原始音频数据
        source_format: 源格式 ('adpcm', 'pcm', 'mp3', 'wav')
        sample_rate: 采样率
        
    Returns:
        WAV格式的音频数据（bytes）
    """
    try:
        # 根据源格式转换为PCM
        if source_format.lower() == 'adpcm':
            pcm_data = adpcm_to_pcm(audio_data)
        elif source_format.lower() == 'mp3':
            pcm_data = mp3_to_pcm(audio_data, sample_rate)
        elif source_format.lower() == 'wav':
            # 如果已经是WAV格式，直接返回
            if isinstance(audio_data, bytes):
                return audio_data
        elif source_format.lower() == 'pcm':
            pcm_data = np.frombuffer(audio_data, dtype=np.int16)
        else:
            raise AudioProcessingException(f"Unsupported source format: {source_format}")
        
        # 转换为WAV格式
        return pcm_to_wav(pcm_data, sample_rate)
    except Exception as e:
        raise AudioProcessingException(f"Audio to WAV conversion failed: {str(e)}")

def base64_to_wav(base64_data: str, format: str = "base64_adpcm", sample_rate: int = 16000):
    """
    将base64编码的音频数据转换为WAV格式
    
    Args:
        base64_data: base64编码的音频数据字符串
        format: 数据格式，支持 "base64_adpcm" 或 "base64_wav"
        sample_rate: 采样率，默认16000Hz
        
    Returns:
        WAV格式的音频数据（bytes）
    """
    try:
        import base64
        
        # 解码base64数据
        try:
            decoded_data = base64.b64decode(base64_data)
        except Exception as e:
            raise AudioProcessingException(f"Base64 decoding failed: {str(e)}")
        
        wav_data = None
        
        if format == "base64_adpcm":
            # 处理ADPCM格式的数据
            try:
                # 使用修改后的adpcm_to_pcm函数进行转换
                pcm_data = adpcm_to_pcm(decoded_data)
                
                # 将PCM数据转换为WAV格式
                wav_data = pcm_to_wav(pcm_data, sample_rate)
                
            except Exception as e:
                raise AudioProcessingException(f"ADPCM to WAV conversion failed: {str(e)}")
        
        elif format == "base64_wav":
            # 处理WAV格式的数据（直接是WAV文件的base64编码）
            try:
                wav_data = decoded_data
                
            except Exception as e:
                raise AudioProcessingException(f"Base64 WAV processing failed: {str(e)}")
        
        else:
            raise AudioProcessingException(f"Unsupported format: {format}. Supported formats are 'base64_adpcm' and 'base64_wav'")
        
        if wav_data is None:
            raise AudioProcessingException("Failed to generate WAV data")
        
        return wav_data
        
    except Exception as e:
        raise AudioProcessingException(f"Base64 to WAV conversion failed: {str(e)}")

def _detect_audio_format(audio_data: bytes) -> str:
    """
    检测音频数据的格式
    
    Args:
        audio_data: 音频数据
        
    Returns:
        检测到的格式 ('wav', 'mp3', 'adpcm', 'pcm')
    """
    try:
        # 检查文件头魔数
        if len(audio_data) < 4:
            return 'pcm'  # 太短的数据默认为PCM
        
        # WAV文件头检测 ('RIFF' 和 'WAVE')
        if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
            return 'wav'
        
        # MP3文件头检测
        # MP3文件通常以ID3标签开头 ('ID3') 或者直接以帧同步字开头
        if audio_data[:3] == b'ID3':
            return 'mp3'
        # MP3帧同步字检测 (11111111 111xxxxx)
        if len(audio_data) >= 2 and audio_data[0] == 0xFF and (audio_data[1] & 0xE0) == 0xE0:
            return 'mp3'
        
        # ADPCM格式检测 (检查是否有 'ADP' 标识)
        if audio_data[:3] == b'ADP':
            return 'adpcm'
        
        # 默认为PCM数据
        return 'pcm'
        
    except Exception as e:
        print(f"音频格式检测失败，默认使用PCM: {str(e)}")
        return 'pcm'