// Audio Analyzer Class for Real-time Audio Detection
// 优化版本：更敏感的音频检测，包含音频保持机制
export class AudioAnalyzer {
    constructor() {
        this.audioContext = null;
        this.analyserNode = null;
        this.mediaStreamSource = null;
        this.dataArray = null;
        this.isAnalyzing = false;
        this.animationId = null;
        
        // 配置参数
        this.fftSize = 256;
        this.smoothingTimeConstant = 0.8;
        this.silenceThreshold = 2;          // 静音阈值 (降低到2，更敏感)
        this.audioThreshold = 5;            // 有音频阈值 (降低到5，更容易触发)
        this.debounceCount = 0;             // 防抖动计数
        this.debounceLimit = 2;             // 防抖动限制 (减少到2次，更快响应)
        this.audioHoldTime = 0;             // 音频保持时间计数
        this.audioHoldLimit = 8;            // 音频保持限制 (检测到音频后保持8次循环)
        
        // 回调函数
        this.onAudioDetected = null;
        this.onSilenceDetected = null;
        this.currentState = 'silence';      // 'silence' | 'audio'
    }
    
    // 初始化音频分析器
    async initialize(mediaStream) {
        try {
            // 创建音频上下文
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // 创建分析器节点
            this.analyserNode = this.audioContext.createAnalyser();
            this.analyserNode.fftSize = this.fftSize;
            this.analyserNode.smoothingTimeConstant = this.smoothingTimeConstant;
            
            // 创建媒体流源
            this.mediaStreamSource = this.audioContext.createMediaStreamSource(mediaStream);
            
            // 连接节点
            this.mediaStreamSource.connect(this.analyserNode);
            
            // 创建数据数组
            const bufferLength = this.analyserNode.frequencyBinCount;
            this.dataArray = new Uint8Array(bufferLength);
            
            console.log('✅ Audio analyzer initialized successfully');
            return true;
        } catch (error) {
            console.error('❌ Failed to initialize audio analyzer:', error);
            return false;
        }
    }
    
    // 开始分析
    startAnalysis() {
        if (!this.analyserNode || this.isAnalyzing) return;
        
        this.isAnalyzing = true;
        this.currentState = 'silence';
        this.debounceCount = 0;
        this.analyzeAudio();
        
        console.log('🎵 Audio analysis started');
    }
    
    // 停止分析
    stopAnalysis() {
        this.isAnalyzing = false;
        
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        
        console.log('🛑 Audio analysis stopped');
    }
    
    // 清理资源
    cleanup() {
        this.stopAnalysis();
        
        if (this.mediaStreamSource) {
            this.mediaStreamSource.disconnect();
            this.mediaStreamSource = null;
        }
        
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        this.analyserNode = null;
        this.dataArray = null;
        
        console.log('🧹 Audio analyzer cleaned up');
    }
    
    // 分析音频数据
    analyzeAudio() {
        if (!this.isAnalyzing || !this.analyserNode) return;
        
        // 获取音频数据
        this.analyserNode.getByteTimeDomainData(this.dataArray);
        
        // 计算音频强度
        const audioLevel = this.calculateAudioLevel();
        
        // 状态判断和防抖动
        this.processAudioLevel(audioLevel);
        
        // 继续分析
        this.animationId = requestAnimationFrame(() => this.analyzeAudio());
    }
    
    // 计算音频强度
    calculateAudioLevel() {
        let sum = 0;
        for (let i = 0; i < this.dataArray.length; i++) {
            const sample = (this.dataArray[i] - 128) / 128;
            sum += sample * sample;
        }
        return Math.sqrt(sum / this.dataArray.length) * 100;
    }
    
    // 处理音频强度并进行防抖动
    processAudioLevel(audioLevel) {
        const hasAudio = audioLevel > this.audioThreshold;
        
        // 如果检测到音频，重置保持时间
        if (hasAudio) {
            this.audioHoldTime = this.audioHoldLimit;
        }
        
        // 确定新状态：有音频或者在保持期内都算作audio状态
        const newState = hasAudio || this.audioHoldTime > 0 ? 'audio' : 'silence';
        
        // 减少保持时间计数
        if (this.audioHoldTime > 0) {
            this.audioHoldTime--;
        }
        
        if (newState !== this.currentState) {
            this.debounceCount++;
            
            if (this.debounceCount >= this.debounceLimit) {
                const previousState = this.currentState;
                this.currentState = newState;
                this.debounceCount = 0;
                
                // 添加更详细的日志
                console.log(`🔄 Audio state changed: ${previousState} → ${newState} (level: ${audioLevel.toFixed(2)}, hold: ${this.audioHoldTime})`);
                
                // 触发回调
                if (newState === 'audio' && this.onAudioDetected) {
                    this.onAudioDetected(audioLevel);
                } else if (newState === 'silence' && this.onSilenceDetected) {
                    this.onSilenceDetected(audioLevel);
                }
            }
        } else {
            this.debounceCount = 0;
        }
    }
    
    // 设置回调函数
    setCallbacks(onAudioDetected, onSilenceDetected) {
        this.onAudioDetected = onAudioDetected;
        this.onSilenceDetected = onSilenceDetected;
    }
    
    // 获取当前状态
    getCurrentState() {
        return this.currentState;
    }
} 