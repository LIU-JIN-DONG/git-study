// BLE音频处理器模块
// 处理来自BLE麦克风的音频数据，支持多种编码格式

import { ADPCMDecoder, resample8to16 } from './adpcm-decoder.js';

export class BLEAudioProcessor extends EventTarget {
    constructor() {
        super();
        this.adpcmDecoder = new ADPCMDecoder();
        this.audioBuffer = [];
        this.isProcessing = false;
        
        // 音频缓冲区设置
        this.bufferSize = 1024; // 缓冲区大小（样本数）
        this.sampleRate = 16000; // 目标采样率
        
        // 原始数据收集（用于调试）
        this.rawDataChunks = [];
    }
    
    // 处理音频数据
    async processAudioData(data, encodeType) {
        console.log(`BLE Audio Processor: Processing ${encodeType} data, length: ${data.length}`);
        
        // 保存原始数据
        this.rawDataChunks.push(new Uint8Array(data));
        
        let pcmData = null;
        
        try {
            switch(encodeType) {
                case 'ADPCM_16K':
                    pcmData = await this.processADPCM16K(data);
                    break;
                    
                case 'ADPCM_8K':
                    pcmData = await this.processADPCM8K(data);
                    break;
                    
                case 'SPEEX':
                    pcmData = await this.processSpeex(data);
                    break;
                    
                case 'OPUS':
                    pcmData = await this.processOpus(data);
                    break;
                    
                default:
                    console.warn(`Unknown encode type: ${encodeType}, trying ADPCM 16K`);
                    pcmData = await this.processADPCM16K(data);
            }
            
            if (pcmData) {
                // 将PCM数据添加到缓冲区
                this.addToBuffer(pcmData);
                
                // 触发音频数据事件
                this.dispatchEvent(new CustomEvent('pcmData', { 
                    detail: { 
                        data: pcmData,
                        sampleRate: this.sampleRate,
                        rawData: data
                    } 
                }));
            }
            
        } catch (error) {
            console.error('BLE Audio Processor: Error processing audio data', error);
            this.dispatchEvent(new CustomEvent('error', { detail: error }));
        }
    }
    
    // 处理 ADPCM 16K 数据
    async processADPCM16K(data) {
        const pcmBytes = this.adpcmDecoder.decodeADPCM16K(data);
        if (!pcmBytes) return null;
        
        // 将字节数组转换为 Int16Array
        const pcmData = new Int16Array(pcmBytes.length / 2);
        for (let i = 0; i < pcmData.length; i++) {
            pcmData[i] = (pcmBytes[i * 2 + 1] << 8) | pcmBytes[i * 2];
        }
        
        console.log(`ADPCM 16K decoded: ${pcmData.length} samples`);
        return pcmData;
    }
    
    // 处理 ADPCM 8K 数据
    async processADPCM8K(data) {
        const pcmBytes = this.adpcmDecoder.decodeADPCM8K(data);
        if (!pcmBytes) return null;
        
        // 将字节数组转换为 Int16Array
        const pcmData8k = new Int16Array(pcmBytes.length / 2);
        for (let i = 0; i < pcmData8k.length; i++) {
            pcmData8k[i] = (pcmBytes[i * 2 + 1] << 8) | pcmBytes[i * 2];
        }
        
        // 重采样到16kHz
        const pcmData16k = resample8to16(pcmData8k);
        
        console.log(`ADPCM 8K decoded and resampled: ${pcmData16k.length} samples`);
        return pcmData16k;
    }
    
    // 处理 Speex 数据（需要外部库）
    async processSpeex(data) {
        console.warn('Speex decoding not implemented yet');
        // TODO: 集成 Speex 解码器
        return null;
    }
    
    // 处理 Opus 数据（需要外部库）
    async processOpus(data) {
        console.warn('Opus decoding not implemented yet');
        // TODO: 集成 Opus 解码器
        return null;
    }
    
    // 添加数据到缓冲区
    addToBuffer(pcmData) {
        // 将新数据添加到缓冲区
        for (let i = 0; i < pcmData.length; i++) {
            this.audioBuffer.push(pcmData[i]);
        }
        
        // 当缓冲区达到指定大小时，触发缓冲区就绪事件
        while (this.audioBuffer.length >= this.bufferSize) {
            const chunk = new Int16Array(this.bufferSize);
            for (let i = 0; i < this.bufferSize; i++) {
                chunk[i] = this.audioBuffer.shift();
            }
            
            this.dispatchEvent(new CustomEvent('bufferReady', { 
                detail: { 
                    buffer: chunk,
                    sampleRate: this.sampleRate
                } 
            }));
        }
    }
    
    // 获取缓冲的音频数据
    getBufferedData() {
        const data = new Int16Array(this.audioBuffer);
        this.audioBuffer = [];
        return data;
    }
    
    // 清空缓冲区
    clearBuffer() {
        this.audioBuffer = [];
        this.rawDataChunks = [];
        this.adpcmDecoder.reset();
    }
    
    // 获取原始数据（用于调试）
    getRawData() {
        // 合并所有原始数据块
        const totalLength = this.rawDataChunks.reduce((sum, chunk) => sum + chunk.length, 0);
        const mergedData = new Uint8Array(totalLength);
        
        let offset = 0;
        for (const chunk of this.rawDataChunks) {
            mergedData.set(chunk, offset);
            offset += chunk.length;
        }
        
        return mergedData;
    }
    
    // 将 PCM 数据转换为 WAV 格式（用于测试）
    createWavBlob(pcmData) {
        const length = pcmData.length * 2;
        const buffer = new ArrayBuffer(44 + length);
        const view = new DataView(buffer);
        
        // WAV 文件头
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        
        writeString(0, 'RIFF');
        view.setUint32(4, 36 + length, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, 1, true);
        view.setUint32(24, this.sampleRate, true);
        view.setUint32(28, this.sampleRate * 2, true);
        view.setUint16(32, 2, true);
        view.setUint16(34, 16, true);
        writeString(36, 'data');
        view.setUint32(40, length, true);
        
        // 写入 PCM 数据
        let offset = 44;
        for (let i = 0; i < pcmData.length; i++) {
            view.setInt16(offset, pcmData[i], true);
            offset += 2;
        }
        
        return new Blob([buffer], { type: 'audio/wav' });
    }
} 