// ADPCM 解码器模块
// 支持 ADPCM 16K 和 ADPCM 8K 格式解码

const indexTable = [
    -1, -1, -1, -1, 2, 4, 6, 8,
    -1, -1, -1, -1, 2, 4, 6, 8
];

const stepsizeTable = [
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17,
    19, 21, 23, 25, 28, 31, 34, 37, 41, 45,
    50, 55, 60, 66, 73, 80, 88, 97, 107, 118,
    130, 143, 157, 173, 190, 209, 230, 253, 279, 307,
    337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
    876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066,
    2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358,
    5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
    15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767
];

export class ADPCMDecoder {
    constructor() {
        this.reset();
    }
    
    reset() {
        this.predictedSample = 0;
        this.stepIndex = 0;
    }
    
    // 解码 ADPCM 16K 格式
    decodeADPCM16K(data) {
        // ADPCM 16K 格式：
        // 前2字节: predict值
        // 第3字节: predict_idx值
        // 第4字节: 有效数据长度
        // 剩余字节: 压缩音频数据
        
        if (data.length < 4) {
            console.error('ADPCM 16K: Invalid data length');
            return null;
        }
        
        // 读取头部信息
        const predictValue = (data[1] << 8) | data[0];
        const predictIdx = data[2];
        const dataLength = data[3];
        
        // 验证数据长度
        if (dataLength > data.length - 4) {
            console.error('ADPCM 16K: Invalid data length in header');
            return null;
        }
        
        // 设置解码器状态
        this.predictedSample = predictValue;
        this.stepIndex = predictIdx;
        
        // 解码音频数据
        const audioData = data.slice(4, 4 + dataLength);
        const pcmData = [];
        
        for (let i = 0; i < audioData.length; i++) {
            const byte = audioData[i];
            // 每个字节包含两个4位的ADPCM样本
            const sample1 = byte & 0x0F;
            const sample2 = (byte >> 4) & 0x0F;
            
            // 解码两个样本
            const pcm1 = this.decodeSample(sample1);
            const pcm2 = this.decodeSample(sample2);
            
            // 转换为16位PCM（小端序）
            pcmData.push(pcm1 & 0xFF, (pcm1 >> 8) & 0xFF);
            pcmData.push(pcm2 & 0xFF, (pcm2 >> 8) & 0xFF);
        }
        
        return new Uint8Array(pcmData);
    }
    
    // 解码 ADPCM 8K 格式
    decodeADPCM8K(data) {
        // ADPCM 8K 格式：
        // 前2字节: "8K" 标识
        // 第3-4字节: predict值
        // 第5字节: predict_idx值
        // 第6字节: 有效数据长度
        // 剩余字节: 压缩音频数据
        
        if (data.length < 6) {
            console.error('ADPCM 8K: Invalid data length');
            return null;
        }
        
        // 验证格式标识
        if (data[0] !== 0x38 || data[1] !== 0x4B) { // "8K"
            console.error('ADPCM 8K: Invalid format identifier');
            return null;
        }
        
        // 读取头部信息
        const predictValue = (data[3] << 8) | data[2];
        const predictIdx = data[4];
        const dataLength = data[5];
        
        // 验证数据长度
        if (dataLength > data.length - 6) {
            console.error('ADPCM 8K: Invalid data length in header');
            return null;
        }
        
        // 设置解码器状态
        this.predictedSample = predictValue;
        this.stepIndex = predictIdx;
        
        // 解码音频数据
        const audioData = data.slice(6, 6 + dataLength);
        const pcmData = [];
        
        for (let i = 0; i < audioData.length; i++) {
            const byte = audioData[i];
            // 每个字节包含两个4位的ADPCM样本
            const sample1 = byte & 0x0F;
            const sample2 = (byte >> 4) & 0x0F;
            
            // 解码两个样本
            const pcm1 = this.decodeSample(sample1);
            const pcm2 = this.decodeSample(sample2);
            
            // 转换为16位PCM（小端序）
            pcmData.push(pcm1 & 0xFF, (pcm1 >> 8) & 0xFF);
            pcmData.push(pcm2 & 0xFF, (pcm2 >> 8) & 0xFF);
        }
        
        return new Uint8Array(pcmData);
    }
    
    // 解码单个ADPCM样本
    decodeSample(nibble) {
        const step = stepsizeTable[this.stepIndex];
        let diff = step >> 3;
        
        if (nibble & 1) diff += step >> 2;
        if (nibble & 2) diff += step >> 1;
        if (nibble & 4) diff += step;
        if (nibble & 8) diff = -diff;
        
        this.predictedSample += diff;
        
        // 限制在16位有符号整数范围内
        if (this.predictedSample > 32767) {
            this.predictedSample = 32767;
        } else if (this.predictedSample < -32768) {
            this.predictedSample = -32768;
        }
        
        // 更新步长索引
        this.stepIndex += indexTable[nibble];
        if (this.stepIndex < 0) {
            this.stepIndex = 0;
        } else if (this.stepIndex > 88) {
            this.stepIndex = 88;
        }
        
        return this.predictedSample;
    }
    
    // 通用解码函数
    decode(data) {
        // 检查是否为 ADPCM 8K 格式
        if (data.length >= 2 && data[0] === 0x38 && data[1] === 0x4B) {
            return this.decodeADPCM8K(data);
        }
        // 否则假定为 ADPCM 16K 格式
        else {
            return this.decodeADPCM16K(data);
        }
    }
}

// 辅助函数：将8kHz音频重采样到16kHz
export function resample8to16(pcmData) {
    const inputLength = pcmData.length;
    const outputLength = inputLength * 2;
    const output = new Int16Array(outputLength);
    
    for (let i = 0; i < inputLength - 1; i++) {
        output[i * 2] = pcmData[i];
        // 线性插值
        output[i * 2 + 1] = Math.round((pcmData[i] + pcmData[i + 1]) / 2);
    }
    
    // 处理最后一个样本
    output[(inputLength - 1) * 2] = pcmData[inputLength - 1];
    output[(inputLength - 1) * 2 + 1] = pcmData[inputLength - 1];
    
    return output;
} 