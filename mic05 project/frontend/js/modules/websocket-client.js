/**
 * WebSocket客户端模块
 * 处理与后端的实时WebSocket通信
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this.messageHandlers = new Map();

        // 音频相关
        this.audioChunks = [];
        this.chunkId = 0;
        this.isRecording = false;
        this.currentAudioId = null;

        this.initMessageHandlers();
        this.initEventListeners();
    }

    /**
     * 初始化消息处理器
     */
    initMessageHandlers() {
        this.messageHandlers.set('connected', this.handleConnected.bind(this));
        this.messageHandlers.set('transcript_result', this.handleTranscriptResult.bind(this));
        this.messageHandlers.set('translation_result', this.handleTranslationResult.bind(this));
        this.messageHandlers.set('tts_audio', this.handleTTSAudio.bind(this));
        this.messageHandlers.set('target_language_changed', this.handleLanguageChanged.bind(this));
        this.messageHandlers.set('tts_stopped', this.handleTTSStopped.bind(this));
        this.messageHandlers.set('error', this.handleError.bind(this));
        this.messageHandlers.set('pong', this.handlePong.bind(this));
        this.messageHandlers.set('system_status', this.handleSystemStatus.bind(this));
    }

    /**
     * 连接WebSocket服务器
     * @param {string} url - WebSocket服务器地址
     */
    async connect(url = 'wss://mic05-demo.hearit.ai/ws') {
        try {
            console.log('🔗 Connecting to WebSocket server:', url);

            this.ws = new WebSocket(url);
            this.setupEventHandlers();

            // 等待连接建立
            await this.waitForConnection();

            console.log('✅ WebSocket connected successfully (no connect message sent)');

        } catch (error) {
            console.error('❌ WebSocket connection failed:', error);
            this.handleConnectionError(error);
        }
    }

    /**
     * 等待WebSocket连接建立
     */
    waitForConnection() {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Connection timeout'));
            }, 10000);

            this.ws.onopen = () => {
                clearTimeout(timeout);
                this.isConnected = true;
                this.reconnectAttempts = 0;
                console.log('✅ WebSocket connected');
                resolve();
            };

            this.ws.onerror = (error) => {
                clearTimeout(timeout);
                reject(error);
            };
        });
    }

    /**
     * 设置WebSocket事件处理器
     */
    setupEventHandlers() {
        this.ws.onmessage = (event) => {
            try {
                // 检查是否是二进制数据
                if (event.data instanceof Blob) {
                    this.handleBinaryMessage(event.data);
                } else {
                    // 处理文本消息（JSON）
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                }
            } catch (error) {
                console.error('❌ Failed to parse message:', error);
            }
        };

        this.ws.onclose = (event) => {
            this.isConnected = false;
            this.stopHeartbeat();
            console.log('🔌 WebSocket disconnected:', event.code, event.reason);

            if (event.code !== 1000) { // 不是正常关闭
                this.attemptReconnect();
            }
        };

        this.ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
        };
    }

    /**
     * 处理收到的消息
     * @param {Object} message - 消息对象
     */
    handleMessage(message) {
        const { type, data } = message;
        console.log('📨 Received message:', type, data);

        const handler = this.messageHandlers.get(type);
        if (handler) {
            handler(data);
        } else {
            console.warn('⚠️ Unknown message type:', type);
        }
    }

    /**
     * 处理二进制消息
     * @param {Blob} binaryData - 二进制数据
     */
    handleBinaryMessage(binaryData) {
        console.log('📦 Received binary data:', binaryData.size, 'bytes');

        // 假设二进制数据是MP3音频数据
        this.handleBinaryTTSAudio(binaryData);
    }

    /**
     * 处理二进制TTS音频数据
     * @param {Blob} audioBlob - 音频Blob数据
     */
    handleBinaryTTSAudio(audioBlob) {
        console.log('🔊 Binary TTS Audio received:', audioBlob.size, 'bytes');

        // 生成音频ID
        const audioId = `tts_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        // 创建音频数据对象
        const audioData = {
            audio_id: audioId,
            audio_blob: audioBlob,
            format: 'mp3',
            is_binary: true,
            text: 'TTS Audio' // 由于是二进制数据，无法获取原始文本
        };

        // 发射TTS音频事件
        this.emit('ttsAudio', audioData);
    }

    // sendConnect方法已删除 - 后端不需要connect消息

    /**
     * 发送音频流
     * @param {string} audioChunk - Base64编码的音频数据
     * @param {boolean} isFinal - 是否是最后一个音频块
     * @param {string} format - 音频格式：'base64_wav' (电脑麦克风) 或 'base64_adpcm' (蓝牙麦克风)
     */
    async sendAudioStream(audioChunk, isFinal = false, format = 'base64_wav') {
        if (!this.isConnected) {
            console.warn('⚠️ WebSocket not connected');
            return;
        }

        const message = {
            type: 'audio_stream',
            data: {
                audio_chunk: audioChunk,
                chunk_id: `chunk_${this.chunkId++}`,
                is_final: isFinal,
                sample_rate: 16000,
                format: format
            }
        };

        await this.sendMessage(message);
    }

    /**
     * 停止TTS播放
     * @param {string} audioId - 音频ID
     */
    async stopTTS(audioId) {
        const message = {
            type: 'stop_tts',
            data: {
                audio_id: audioId
            }
        };

        await this.sendMessage(message);
    }

    /**
     * 发送心跳
     */
    async sendPing() {
        const message = {
            type: 'ping',
            data: {
                timestamp: new Date().toISOString()
            }
        };

        await this.sendMessage(message);
    }

    /**
     * 发送消息
     * @param {Object} message - 消息对象
     */
    async sendMessage(message) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('⚠️ WebSocket not ready');
            return;
        }

        // 验证消息格式
        if (!message || !message.type) {
            console.error('❌ Invalid message format:', message);
            return;
        }

        // 支持的消息类型列表（与后端兼容）
        const supportedTypes = ['audio_stream', 'stop_tts', 'ping'];
        if (!supportedTypes.includes(message.type)) {
            console.warn('⚠️ Potentially unsupported message type:', message.type);
        }

        try {
            this.ws.send(JSON.stringify(message));
            console.log('📤 Sent message:', message.type);
        } catch (error) {
            console.error('❌ Failed to send message:', error);
        }
    }

    /**
     * 开始心跳检测
     */
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.sendPing();
            }
        }, 30000); // 每30秒发送心跳
    }

    /**
     * 停止心跳检测
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * 尝试重连
     */
    async attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ Maximum reconnection attempts reached');
            this.emit('maxReconnectAttemptsReached');
            return;
        }

        this.reconnectAttempts++;
        console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay * this.reconnectAttempts);
    }

    /**
     * 处理连接错误
     * @param {Error} error - 错误对象
     */
    handleConnectionError(error) {
        console.error('❌ Connection error:', error);
        this.emit('connectionError', error);
    }

    /**
     * 断开连接
     */
    disconnect() {
        if (this.ws) {
            this.stopHeartbeat();
            this.ws.close(1000, 'Client disconnecting');
            this.ws = null;
            this.isConnected = false;
            this.sessionId = null;
        }
    }

    // =================================
    // 消息处理器
    // =================================

    /**
     * 处理连接确认消息
     * @param {Object} data - 消息数据
     */
    handleConnected(data) {
        this.sessionId = data.session_id;
        this.startHeartbeat();
        console.log('✅ Connected with session ID:', this.sessionId);
        this.emit('connected', data);
    }

    /**
     * 处理转录结果
     * @param {Object} data - 转录数据
     */
    handleTranscriptResult(data) {
        console.log('🎤 Transcript:', data.text, data.is_final ? '(final)' : '(partial)');
        this.emit('transcript', data);
    }

    /**
     * 处理翻译结果
     * @param {Object} data - 翻译数据
     */
    handleTranslationResult(data) {
        console.log('🌍 Translation:', data.source_text, '->', data.target_text);
        this.emit('translation', data);
    }

    /**
     * 处理TTS音频
     * @param {Object} data - TTS音频数据
     */
    handleTTSAudio(data) {
        console.log('🔊 TTS Audio received:', data.audio_id);
        this.currentAudioId = data.audio_id;
        this.emit('ttsAudio', data);
    }

    /**
     * 处理语言变更
     * @param {Object} data - 语言变更数据
     */
    handleLanguageChanged(data) {
        console.log('🌍 Language changed:', data.previous_language, '->', data.current_language);
        this.emit('languageChanged', data);
    }

    /**
     * 处理TTS停止
     * @param {Object} data - TTS停止数据
     */
    handleTTSStopped(data) {
        console.log('⏹️ TTS stopped:', data.audio_id);
        this.emit('ttsStopped', data);
    }

    /**
     * 处理错误消息
     * @param {Object} data - 错误数据
     */
    handleError(data) {
        // 兼容不同的错误消息格式
        const errorCode = data.error_code || data.error || 'UNKNOWN_ERROR';
        const errorMessage = data.message || data.error_message || errorCode;
        
        console.error('❌ Server error:', errorCode, errorMessage);
        
        // 发出统一格式的错误事件
        this.emit('error', {
            error_code: errorCode,
            message: errorMessage,
            original: data
        });
    }

    /**
     * 处理心跳响应
     * @param {Object} data - 心跳数据
     */
    handlePong(data) {
        console.log('💓 Pong received, server load:', data.server_load);
        this.emit('pong', data);
    }

    /**
     * 处理系统状态
     * @param {Object} data - 系统状态数据
     */
    handleSystemStatus(data) {
        console.log('📊 System status:', data);
        this.emit('systemStatus', data);
    }

    // =================================
    // 事件发射器
    // =================================

    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        this.eventListeners = new Map();
    }

    /**
     * 添加事件监听器
     * @param {string} event - 事件名称
     * @param {Function} listener - 监听器函数
     */
    on(event, listener) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(listener);
    }

    /**
     * 移除事件监听器
     * @param {string} event - 事件名称
     * @param {Function} listener - 监听器函数
     */
    off(event, listener) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(listener);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * 发射事件
     * @param {string} event - 事件名称
     * @param {*} data - 事件数据
     */
    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(listener => {
                try {
                    listener(data);
                } catch (error) {
                    console.error('❌ Event listener error:', error);
                }
            });
        }
    }

    // =================================
    // 获取器
    // =================================

    /**
     * 获取连接状态
     */
    get connected() {
        return this.isConnected;
    }

    /**
     * 获取会话ID
     */
    get session() {
        return this.sessionId;
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
} else {
    window.WebSocketClient = WebSocketClient;
} 