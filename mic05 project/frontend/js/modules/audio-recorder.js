/**
 * 音频录制模块
 * 处理音频录制、播放和格式转换
 * 支持系统麦克风和BLE麦克风输入
 */

import { BLEMicrophone } from './bluetooth/ble-microphone.js';
import { BLEAudioProcessor } from './bluetooth/ble-audio-processor.js';

class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.isPaused = false;
        this.audioContext = null;
        this.processor = null;
        this.eventListeners = new Map();

        // 输入源类型: 'system' | 'bluetooth'
        this.inputType = 'system';

        // BLE相关
        this.bleMicrophone = null;
        this.bleAudioProcessor = null;
        this.isBLERecording = false;

        // WebSocket相关
        this.wsClient = null;

        // 数据收集功能
        this.dataCollectionEnabled = false;
        this.collectedData = {
            system: {
                audioBlob: null,
                audioChunks: [],
                base64Data: [],
                base64Complete: '',
                recordingStartTime: null,
                recordingEndTime: null
            },
            bluetooth: {
                rawDataChunks: [],
                base64Data: [],
                base64Complete: '',
                recordingStartTime: null,
                recordingEndTime: null
            }
        };

        // 录制设置
        this.config = {
            sampleRate: 16000,
            channels: 1,
            bitsPerSample: 16,
            format: 'wav'
        };

        // 音频播放
        this.audioElements = new Map();
        this.currentPlayback = null;

        this.initEventListeners();
    }

    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        this.eventListeners = new Map();
    }

    /**
     * 初始化录制器
     */
    async initialize() {
        try {
            // 请求麦克风权限
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.config.sampleRate,
                    channelCount: this.config.channels,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            console.log('✅ Audio stream initialized');
            this.emit('initialized');
            return true;
        } catch (error) {
            console.error('❌ Failed to initialize audio:', error);
            this.emit('error', { type: 'initialization', error });
            return false;
        }
    }

    /**
     * 设置WebSocket客户端
     * @param {WebSocketClient} wsClient - WebSocket客户端实例
     */
    setWebSocketClient(wsClient) {
        this.wsClient = wsClient;
    }

    /**
     * 启用数据收集功能
     * @param {boolean} enabled - 是否启用数据收集
     */
    enableDataCollection(enabled = true) {
        this.dataCollectionEnabled = enabled;
        console.log(`📊 Data collection ${enabled ? 'enabled' : 'disabled'}`);

        if (enabled) {
            this.clearCollectedData();
        }
    }

    /**
     * 清理收集的数据
     */
    clearCollectedData() {
        this.collectedData = {
            system: {
                audioBlob: null,
                audioChunks: [],
                base64Data: [],
                base64Complete: '',
                recordingStartTime: null,
                recordingEndTime: null
            },
            bluetooth: {
                rawDataChunks: [],
                base64Data: [],
                base64Complete: '',
                recordingStartTime: null,
                recordingEndTime: null
            }
        };
        console.log('🗑️ Collected data cleared');
    }

    /**
     * 获取收集的数据
     * @returns {Object} 收集的数据对象
     */
    getCollectedData() {
        return this.collectedData;
    }

    /**
     * 下载系统麦克风音频文件
     * @param {string} filename - 文件名（不包括扩展名）
     */
    downloadSystemAudio(filename = 'system_microphone_audio') {
        if (!this.collectedData.system.audioBlob) {
            console.warn('⚠️ No system audio data to download');
            return;
        }

        const url = URL.createObjectURL(this.collectedData.system.audioBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}.webm`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log('📥 System audio downloaded:', `${filename}.webm`);
    }

    /**
     * 下载蓝牙麦克风原始数据
     * @param {string} filename - 文件名（不包括扩展名）
     */
    downloadBluetoothRawData(filename = 'bluetooth_microphone_raw') {
        if (!this.collectedData.bluetooth.rawDataChunks.length) {
            console.warn('⚠️ No bluetooth raw data to download');
            return;
        }

        // 合并所有原始数据
        const totalLength = this.collectedData.bluetooth.rawDataChunks.reduce((sum, chunk) => sum + chunk.length, 0);
        const combinedData = new Uint8Array(totalLength);
        let offset = 0;

        for (const chunk of this.collectedData.bluetooth.rawDataChunks) {
            combinedData.set(chunk, offset);
            offset += chunk.length;
        }

        const blob = new Blob([combinedData], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}.adpcm`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log('📥 Bluetooth raw data downloaded:', `${filename}.adpcm`);
    }

    /**
     * 下载base64数据文件
     * @param {string} type - 数据类型：'system' 或 'bluetooth'
     * @param {string} filename - 文件名（不包括扩展名）
     */
    downloadBase64Data(type, filename = null) {
        if (!['system', 'bluetooth'].includes(type)) {
            console.error('❌ Invalid data type. Use "system" or "bluetooth"');
            return;
        }

        const data = this.collectedData[type];
        if (!data.base64Complete) {
            console.warn(`⚠️ No ${type} base64 data to download`);
            return;
        }

        const defaultFilename = type === 'system' ? 'system_microphone_base64' : 'bluetooth_microphone_base64';
        const finalFilename = filename || defaultFilename;

        const blob = new Blob([data.base64Complete], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${finalFilename}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log('📥 Base64 data downloaded:', `${finalFilename}.txt`);
    }

    /**
     * 下载所有收集的数据
     * @param {string} prefix - 文件名前缀
     */
    downloadAllCollectedData(prefix = 'audio_recording') {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const filenamePrefix = `${prefix}_${timestamp}`;

        // 下载系统麦克风数据
        if (this.collectedData.system.audioBlob) {
            this.downloadSystemAudio(`${filenamePrefix}_system`);
        }
        if (this.collectedData.system.base64Complete) {
            this.downloadBase64Data('system', `${filenamePrefix}_system_base64`);
        }

        // 下载蓝牙麦克风数据
        if (this.collectedData.bluetooth.rawDataChunks.length) {
            this.downloadBluetoothRawData(`${filenamePrefix}_bluetooth`);
        }
        if (this.collectedData.bluetooth.base64Complete) {
            this.downloadBase64Data('bluetooth', `${filenamePrefix}_bluetooth_base64`);
        }

        console.log('📥 All collected data downloaded with prefix:', filenamePrefix);
    }

    /**
     * 切换到蓝牙输入
     */
    async switchToBluetooth() {
        try {
            console.log('🔄 Switching to Bluetooth input...');

            // 如果正在录制，先停止
            if (this.isRecording) {
                this.stopRecording();
            }

            // 创建BLE麦克风实例
            if (!this.bleMicrophone) {
                this.bleMicrophone = new BLEMicrophone();
                this.bleAudioProcessor = new BLEAudioProcessor();

                // 设置BLE事件监听器
                this.setupBLEEventListeners();
            }

            // 连接BLE设备
            const connected = await this.bleMicrophone.connect();
            if (!connected) {
                throw new Error('Failed to connect to BLE device');
            }

            this.inputType = 'bluetooth';
            console.log('✅ Switched to Bluetooth input');
            this.emit('inputSourceChanged', { source: 'bluetooth' });

            return true;
        } catch (error) {
            console.error('❌ Failed to switch to Bluetooth:', error);
            this.emit('error', { type: 'bluetoothSwitch', error });
            return false;
        }
    }

    /**
     * 连接指定的蓝牙设备
     * @param {BluetoothDevice} device - 已经通过navigator.bluetooth.requestDevice获取的设备
     */
    async connectBluetoothDevice(device) {
        try {
            console.log('🔄 Connecting to Bluetooth device:', device.name);

            // 如果正在录制，先停止
            if (this.isRecording) {
                this.stopRecording();
            }

            // 创建或重置BLE麦克风实例
            if (!this.bleMicrophone) {
                console.log('🔧 Creating new BLE microphone instance');
                this.bleMicrophone = new BLEMicrophone();
                this.bleAudioProcessor = new BLEAudioProcessor();
            } else {
                console.log('🔧 Resetting existing BLE microphone instance');
                // 如果已存在，重置状态以确保干净的连接
                this.bleMicrophone.reset();
            }

            // 始终重新设置BLE事件监听器（确保连接新设备时正确绑定）
            console.log('🔧 Setting up BLE event listeners');
            this.setupBLEEventListeners();

            // 使用指定的设备连接
            console.log('🔧 Attempting to connect to device...');
            const connected = await this.bleMicrophone.connectToDevice(device);
            if (!connected) {
                throw new Error('Failed to connect to the specified BLE device');
            }

            this.inputType = 'bluetooth';
            console.log('✅ Connected to Bluetooth device:', device.name);
            
            // 验证连接状态和服务可用性
            console.log('🔍 Audio Recorder Connection verification:');
            console.log('  - BLE microphone connected:', this.bleMicrophone.isConnected);
            console.log('  - GATT server:', !!this.bleMicrophone.gattServer);
            console.log('  - Voice service:', !!this.bleMicrophone.voiceService);
            console.log('  - Voice data characteristic:', !!this.bleMicrophone.voiceDataCharacteristic);
            console.log('  - Function model characteristic:', !!this.bleMicrophone.functionModelCharacteristic);
            console.log('  - Input type set to:', this.inputType);
            console.log('  - Event listeners bound:', !!this._bleEventListeners);
            console.log('  - Event listeners count:', this._bleEventListeners?.length || 0);
            
            this.emit('inputSourceChanged', { source: 'bluetooth', device: device });

            return true;
        } catch (error) {
            console.error('❌ Failed to connect Bluetooth device:', error);
            this.emit('error', { type: 'bluetoothConnect', error });
            return false;
        }
    }

    /**
     * 切换到系统麦克风
     */
    async switchToSystem() {
        try {
            console.log('🔄 Switching to system microphone...');

            // 如果正在BLE录制，先停止
            if (this.isBLERecording) {
                this.stopBLERecording();
            }

            // 断开BLE连接
            if (this.bleMicrophone && this.bleMicrophone.isConnected) {
                this.bleMicrophone.disconnect();
            }

            this.inputType = 'system';
            console.log('✅ Switched to system microphone');
            this.emit('inputSourceChanged', { source: 'system' });

            return true;
        } catch (error) {
            console.error('❌ Failed to switch to system microphone:', error);
            this.emit('error', { type: 'systemSwitch', error });
            return false;
        }
    }

    /**
     * 设置BLE事件监听器
     */
    setupBLEEventListeners() {
        // 先移除所有现有的事件监听器（防止重复绑定）
        if (this.bleMicrophone && this._bleEventListeners) {
            this._bleEventListeners.forEach(({ event, listener }) => {
                this.bleMicrophone.removeEventListener(event, listener);
            });
        }
        
        // 存储事件监听器引用，以便稍后移除
        this._bleEventListeners = [];
        
        // BLE连接事件
        const connectedListener = (event) => {
            console.log('🔗 BLE connected:', event.detail);
            this.emit('bleConnected', event.detail);
        };

        const disconnectedListener = () => {
            console.log('❌ BLE disconnected');
            this.emit('bleDisconnected');
            // 自动切换回系统麦克风
            if (this.inputType === 'bluetooth') {
                this.switchToSystem();
            }
        };

        // BLE按键事件
        const buttonEventListener = (event) => {
            console.log('🔘 BLE button event:', event.detail);
            this.emit('bleButtonEvent', event.detail);

            const value = event.detail.value;

            // 录音开始（按键值1）
            if (value === 1 && !this.isBLERecording) {
                this.startBLERecording();
            }
            // 录音结束（按键值0）
            else if (value === 0 && this.isBLERecording) {
                console.log('🔘 BLE button released, stopping recording...');
                this.stopBLERecording();
            }
        };

        // BLE录音结束事件 - 增加额外监听以确保可靠性
        const recordingEndListener = () => {
            console.log('🔘 BLE recordingEnd event received');
            if (this.isBLERecording) {
                console.log('🔘 Stopping BLE recording from recordingEnd event');
                this.stopBLERecording();
            }
        };

        // BLE音频数据事件 - 直接传输原始数据，不解码
        const audioDataListener = async (event) => {
            if (this.isBLERecording) {
                const { data, encodeType } = event.detail;

                // 打印原始音频数据信息
                console.log('🎵 BLE Raw Audio Data:', {
                    encodeType: encodeType,
                    dataLength: data.length,
                    rawDataHex: Array.from(data.slice(0, 20)).map(b => '0x' + b.toString(16).padStart(2, '0')).join(' ')
                });

                // 将原始数据转换为base64格式
                const base64Data = this.arrayBufferToBase64(data.buffer);

                // 如果启用了数据收集，保存原始数据和base64数据
                if (this.dataCollectionEnabled) {
                    this.collectedData.bluetooth.rawDataChunks.push(new Uint8Array(data));
                    this.collectedData.bluetooth.base64Data.push(base64Data);
                }

                // 发送到WebSocket
                if (this.wsClient && this.wsClient.isConnected) {
                    this.wsClient.sendAudioStream(base64Data, false, 'base64_adpcm');
                }

                // 发射原始音频数据事件
                this.emit('bleRawAudioData', { data, encodeType });
            }
        };

        // 绑定所有事件监听器
        this.bleMicrophone.addEventListener('connected', connectedListener);
        this.bleMicrophone.addEventListener('disconnected', disconnectedListener);
        this.bleMicrophone.addEventListener('buttonEvent', buttonEventListener);
        this.bleMicrophone.addEventListener('recordingEnd', recordingEndListener);
        this.bleMicrophone.addEventListener('audioData', audioDataListener);

        // 存储事件监听器引用，以便稍后移除
        this._bleEventListeners = [
            { event: 'connected', listener: connectedListener },
            { event: 'disconnected', listener: disconnectedListener },
            { event: 'buttonEvent', listener: buttonEventListener },
            { event: 'recordingEnd', listener: recordingEndListener },
            { event: 'audioData', listener: audioDataListener }
        ];

        console.log('🔧 BLE event listeners bound successfully');

        // 注意：不再使用BLE音频处理器的pcmData和bufferReady事件
        // 原始音频数据将直接在audioData事件中处理和发送
    }

    /**
     * 开始BLE录制
     */
    startBLERecording() {
        if (!this.bleMicrophone || !this.bleMicrophone.isConnected) {
            console.error('❌ BLE microphone not connected');
            return false;
        }

        this.isBLERecording = true;
        this.isRecording = true; // 设置通用录音状态标志
        this.isBLERecordingStartTime = Date.now(); // 记录开始时间

        // 如果启用了数据收集，清理并初始化蓝牙麦克风数据
        if (this.dataCollectionEnabled) {
            this.collectedData.bluetooth.rawDataChunks = [];
            this.collectedData.bluetooth.base64Data = [];
            this.collectedData.bluetooth.base64Complete = '';
            this.collectedData.bluetooth.recordingStartTime = Date.now();
            this.collectedData.bluetooth.recordingEndTime = null;
            console.log('📊 Started collecting Bluetooth microphone data');
        }

        console.log('🎤 BLE recording started - sending raw audio data to backend');
        this.emit('recordingStarted', { source: 'bluetooth' });

        return true;
    }

    /**
     * 停止BLE录制
     */
    stopBLERecording() {
        if (!this.isBLERecording) {
            console.log('⚠️ BLE recording not active');
            return false;
        }

        this.isBLERecording = false;
        this.isRecording = false; // 清除通用录音状态标志

        // 如果启用了数据收集，完成蓝牙麦克风数据收集
        if (this.dataCollectionEnabled) {
            this.collectedData.bluetooth.recordingEndTime = Date.now();

            // 合并所有base64数据
            if (this.collectedData.bluetooth.base64Data.length > 0) {
                this.collectedData.bluetooth.base64Complete = this.collectedData.bluetooth.base64Data.join('');
            }

            const duration = this.collectedData.bluetooth.recordingEndTime - this.collectedData.bluetooth.recordingStartTime;
            console.log(`📊 Bluetooth microphone data collected: ${this.collectedData.bluetooth.rawDataChunks.length} chunks, ${duration}ms duration`);
        }

        console.log('🎤 BLE recording stopped');
        this.emit('recordingComplete', {
            source: 'bluetooth',
            duration: Date.now() - this.isBLERecordingStartTime,
            chunks: this.dataCollectionEnabled ? this.collectedData.bluetooth.rawDataChunks.length : 0
        });

        return true;
    }

    /**
     * 开始录制（根据输入源自动选择）
     */
    async startRecording() {
        if (this.inputType === 'bluetooth') {
            return this.startBLERecording();
        } else {
            // 原有的系统麦克风录制逻辑
            return this.startSystemRecording();
        }
    }

    /**
     * 停止录制（根据输入源自动选择）
     */
    stopRecording() {
        if (this.inputType === 'bluetooth') {
            this.stopBLERecording();
        } else {
            // 原有的停止逻辑
            this.stopSystemRecording();
        }
    }

    /**
     * 开始系统麦克风录制（原有的startRecording方法）
     */
    async startSystemRecording() {
        try {
            if (!this.audioStream) {
                const initialized = await this.initialize();
                if (!initialized) {
                    throw new Error('Failed to initialize audio stream');
                }
            }

            this.audioChunks = [];

            // 如果启用了数据收集，清理并初始化系统麦克风数据
            if (this.dataCollectionEnabled) {
                this.collectedData.system.audioChunks = [];
                this.collectedData.system.base64Data = [];
                this.collectedData.system.base64Complete = '';
                this.collectedData.system.recordingStartTime = Date.now();
                this.collectedData.system.recordingEndTime = null;
                console.log('📊 Started collecting system microphone data');
            }

            // 创建MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            // 设置事件监听器
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);

                    // 如果启用了数据收集，保存音频块
                    if (this.dataCollectionEnabled) {
                        this.collectedData.system.audioChunks.push(event.data);
                    }

                    this.processAudioChunk(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.processRecordingComplete();
            };

            this.mediaRecorder.onerror = (error) => {
                console.error('❌ MediaRecorder error:', error);
                this.emit('error', { type: 'recording', error });
            };

            // 开始录制
            this.mediaRecorder.start(250); // 每250ms生成一个数据块
            this.isRecording = true;
            this.isPaused = false;

            console.log('🎤 Recording started');
            this.emit('recordingStarted', { source: 'system' });

            return true;
        } catch (error) {
            console.error('❌ Failed to start recording:', error);
            this.emit('error', { type: 'startRecording', error });
            return false;
        }
    }

    /**
     * 停止系统麦克风录制（原有的stopRecording方法）
     */
    stopSystemRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.isPaused = false;

            console.log('⏹️ Recording stopped');
            this.emit('recordingStopped', { source: 'system' });
        }
    }

    /**
     * 暂停录制
     */
    pauseRecording() {
        if (this.mediaRecorder && this.isRecording && !this.isPaused) {
            this.mediaRecorder.pause();
            this.isPaused = true;

            console.log('⏸️ Recording paused');
            this.emit('recordingPaused');
        }
    }

    /**
     * 恢复录制
     */
    resumeRecording() {
        if (this.mediaRecorder && this.isRecording && this.isPaused) {
            this.mediaRecorder.resume();
            this.isPaused = false;

            console.log('▶️ Recording resumed');
            this.emit('recordingResumed');
        }
    }

    /**
     * 处理音频块
     * @param {Blob} audioBlob - 音频数据块
     */
    async processAudioChunk(audioBlob) {
        try {
            // 转换为Base64
            const base64Data = await this.blobToBase64(audioBlob);

            // 如果启用了数据收集，保存base64数据
            if (this.dataCollectionEnabled) {
                this.collectedData.system.base64Data.push(base64Data);
            }

            // 发射音频块事件
            this.emit('audioChunk', {
                blob: audioBlob,
                base64: base64Data,
                timestamp: Date.now()
            });

        } catch (error) {
            console.error('❌ Failed to process audio chunk:', error);
            this.emit('error', { type: 'processing', error });
        }
    }

    /**
     * 处理录制完成
     */
    async processRecordingComplete() {
        try {
            // 合并所有音频块
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm;codecs=opus' });
            const base64Data = await this.blobToBase64(audioBlob);

            // 如果启用了数据收集，保存完整数据
            if (this.dataCollectionEnabled) {
                this.collectedData.system.audioBlob = audioBlob;
                this.collectedData.system.base64Complete = base64Data;
                this.collectedData.system.recordingEndTime = Date.now();

                const duration = this.collectedData.system.recordingEndTime - this.collectedData.system.recordingStartTime;
                console.log(`📊 System microphone data collected: ${this.collectedData.system.audioChunks.length} chunks, ${duration}ms duration`);
            }

            // 发射录制完成事件
            this.emit('recordingComplete', {
                blob: audioBlob,
                base64: base64Data,
                duration: this.getRecordingDuration(),
                chunks: this.audioChunks.length
            });

        } catch (error) {
            console.error('❌ Failed to process recording complete:', error);
            this.emit('error', { type: 'completion', error });
        }
    }

    /**
     * 播放音频
     * @param {string} audioData - Base64编码的音频数据
     * @param {string} format - 音频格式 (mp3, wav, etc.)
     * @param {string} audioId - 音频ID
     */
    async playAudio(audioData, format = 'mp3', audioId = null) {
        try {
            // 创建音频元素
            const audio = new Audio();
            const audioId_final = audioId || `audio_${Date.now()}`;

            // 创建音频URL
            const audioUrl = `data:audio/${format};base64,${audioData}`;
            audio.src = audioUrl;

            // 存储音频元素
            this.audioElements.set(audioId_final, audio);

            // 设置事件监听器
            audio.onloadeddata = () => {
                console.log('🔊 Audio loaded:', audioId_final);
                this.emit('audioLoaded', { audioId: audioId_final });
            };

            audio.onplay = () => {
                this.currentPlayback = audioId_final;
                console.log('▶️ Audio started playing:', audioId_final);
                this.emit('audioPlaying', { audioId: audioId_final });
            };

            audio.onpause = () => {
                console.log('⏸️ Audio paused:', audioId_final);
                this.emit('audioPaused', { audioId: audioId_final });
            };

            audio.onended = () => {
                this.currentPlayback = null;
                console.log('⏹️ Audio ended:', audioId_final);
                this.emit('audioEnded', { audioId: audioId_final });

                // 清理音频元素
                this.audioElements.delete(audioId_final);
            };

            audio.onerror = (error) => {
                console.error('❌ Audio playback error:', error);
                this.emit('error', { type: 'playback', error, audioId: audioId_final });
            };

            // 播放音频
            await audio.play();

            return audioId_final;

        } catch (error) {
            console.error('❌ Failed to play audio:', error);
            this.emit('error', { type: 'playback', error });
            return null;
        }
    }

    /**
     * 停止音频播放
     * @param {string} audioId - 音频ID
     */
    stopAudio(audioId) {
        if (this.audioElements.has(audioId)) {
            const audio = this.audioElements.get(audioId);
            audio.pause();
            audio.currentTime = 0;

            console.log('⏹️ Audio stopped:', audioId);
            this.emit('audioStopped', { audioId });
        }
    }

    /**
     * 停止所有音频播放
     */
    stopAllAudio() {
        this.audioElements.forEach((audio, audioId) => {
            audio.pause();
            audio.currentTime = 0;
            this.emit('audioStopped', { audioId });
        });

        this.audioElements.clear();
        this.currentPlayback = null;
        console.log('⏹️ All audio stopped');
    }

    /**
     * 获取录制时长
     */
    getRecordingDuration() {
        // 简单估算，实际应该基于音频数据计算
        return this.audioChunks.length * 250; // 每个chunk 250ms
    }

    /**
     * 将Blob转换为Base64
     * @param {Blob} blob - 音频Blob对象
     */
    blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    /**
     * 将ArrayBuffer转换为Base64
     * @param {ArrayBuffer} buffer - 要转换的ArrayBuffer
     * @returns {string} Base64编码的字符串
     */
    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    /**
     * 将Int16Array转换为字节数组（小端序）
     * @param {Int16Array} int16Array - 16位PCM样本数组
     * @returns {Uint8Array} 字节数组
     */
    int16ArrayToBytes(int16Array) {
        const bytes = new Uint8Array(int16Array.length * 2);
        for (let i = 0; i < int16Array.length; i++) {
            const sample = int16Array[i];
            // 小端序：低字节在前
            bytes[i * 2] = sample & 0xFF;           // 低字节
            bytes[i * 2 + 1] = (sample >> 8) & 0xFF; // 高字节
        }
        return bytes;
    }

    /**
     * 检查浏览器支持
     */
    static checkSupport() {
        const support = {
            mediaRecorder: typeof MediaRecorder !== 'undefined',
            getUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
            audioContext: !!(window.AudioContext || window.webkitAudioContext),
            webAudio: !!(window.AudioContext || window.webkitAudioContext)
        };

        console.log('🔍 Browser audio support:', support);
        return support;
    }

    /**
     * 获取可用的音频设备
     */
    async getAudioDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioInputs = devices.filter(device => device.kind === 'audioinput');
            const audioOutputs = devices.filter(device => device.kind === 'audiooutput');

            return {
                inputs: audioInputs,
                outputs: audioOutputs
            };
        } catch (error) {
            console.error('❌ Failed to get audio devices:', error);
            return { inputs: [], outputs: [] };
        }
    }

    /**
     * 切换音频设备
     * @param {string} deviceId - 设备ID
     */
    async switchAudioDevice(deviceId) {
        try {
            // 停止当前流
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
            }

            // 创建新的流
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    deviceId: { exact: deviceId },
                    sampleRate: this.config.sampleRate,
                    channelCount: this.config.channels,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            console.log('✅ Audio device switched:', deviceId);
            this.emit('deviceChanged', { deviceId });

        } catch (error) {
            console.error('❌ Failed to switch audio device:', error);
            this.emit('error', { type: 'deviceSwitch', error });
        }
    }

    /**
     * 获取BLE设备信息
     */
    getBLEDeviceInfo() {
        if (this.bleMicrophone && this.bleMicrophone.isConnected) {
            return {
                connected: true,
                device: this.bleMicrophone.device.name,
                systemId: this.bleMicrophone.systemId,
                encodeType: this.bleMicrophone.defaultEncodeType
            };
        }
        return {
            connected: false,
            device: null,
            systemId: null,
            encodeType: null
        };
    }

    /**
     * 清理资源
     */
    cleanup() {
        // 停止录制
        if (this.isRecording || this.isBLERecording) {
            this.stopRecording();
        }

        // 停止所有音频播放
        this.stopAllAudio();

        // 停止音频流
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }

        // 清理音频上下文
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        // 断开BLE连接
        if (this.bleMicrophone && this.bleMicrophone.isConnected) {
            this.bleMicrophone.disconnect();
        }

        console.log('🧹 Audio recorder cleaned up');
    }

    // =================================
    // 事件发射器
    // =================================

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
     * 获取录制状态
     */
    get recording() {
        return this.isRecording;
    }

    /**
     * 获取暂停状态
     */
    get paused() {
        return this.isPaused;
    }

    /**
     * 获取当前播放的音频ID
     */
    get currentAudio() {
        return this.currentPlayback;
    }

    /**
     * 获取音频流状态
     */
    get hasAudioStream() {
        return !!this.audioStream;
    }
}

// 导出模块
export { AudioRecorder };

// 也暴露到全局作用域以便兼容非模块化使用
if (typeof window !== 'undefined') {
    window.AudioRecorder = AudioRecorder;
} 