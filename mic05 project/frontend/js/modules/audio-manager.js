/**
 * 音频管理器组件
 * 统一管理所有音频播放功能，避免重叠播放
 */
class AudioManager {
    constructor() {
        this.audioRecorder = null;
        this.currentAudioElement = null;
        this.isPlaying = false;
        this.currentAudioId = null;
        
        this.init();
    }

    init() {
        // 等待audioRecorder初始化
        this.waitForAudioRecorder();
    }

    waitForAudioRecorder() {
        let attempts = 0;
        const maxAttempts = 50; // 最多等待5秒
        
        const checkRecorder = () => {
            attempts++;
            
            if (window.audioRecorder) {
                this.audioRecorder = window.audioRecorder;
                this.setupEventListeners();
                console.log('✅ AudioManager found AudioRecorder after', attempts, 'attempts');
                return;
            }
            
            if (attempts >= maxAttempts) {
                console.warn('❌ AudioManager: AudioRecorder not found after', maxAttempts, 'attempts');
                return;
            }
            
            console.log('⏳ AudioManager waiting for AudioRecorder... attempt', attempts);
            setTimeout(checkRecorder, 100);
        };
        
        checkRecorder();
    }

    setupEventListeners() {
        if (this.audioRecorder) {
            // 监听AudioRecorder的播放事件
            this.audioRecorder.on('audioPlaying', (data) => {
                this.handleAudioPlaying(data.audioId);
            });

            this.audioRecorder.on('audioEnded', (data) => {
                this.handleAudioEnded(data.audioId);
            });

            this.audioRecorder.on('audioStopped', (data) => {
                this.handleAudioStopped(data.audioId);
            });
        }
    }

    /**
     * 处理TTS音频数据
     * @param {Object} data - 音频数据
     */
    handleTTSAudio(data) {
        console.log('🎵 Audio Manager handling TTS audio:', data.audio_id);

        // 停止所有当前播放的音频，避免重叠播放
        this.stopAllAudio();

        // 处理二进制音频数据
        if (data.is_binary && data.audio_blob) {
            this.playBinaryAudio(data);
            return;
        }

        // 处理base64格式音频数据
        if (data.audio_data) {
            this.playBase64Audio(data);
        }
    }

    /**
     * 播放二进制音频
     * @param {Object} data - 音频数据
     */
    playBinaryAudio(data) {
        console.log('🎵 Playing binary MP3 audio:', data.audio_blob.size, 'bytes');
        
        const audioUrl = URL.createObjectURL(data.audio_blob);
        const audio = new Audio(audioUrl);
        this.currentAudioElement = audio;
        this.currentAudioId = data.audio_id;

        // 设置事件监听器
        audio.onloadstart = () => {
            console.log('🔊 Audio loading started:', data.audio_id);
            this.updatePlaybackUI(data.audio_id, true);
        };

        audio.onplay = () => {
            console.log('🔊 Audio started playing:', data.audio_id);
            this.isPlaying = true;
            this.updatePlaybackUI(data.audio_id, true);
        };

        audio.onended = () => {
            console.log('🔊 Audio playback ended:', data.audio_id);
            this.handleAudioEnded(data.audio_id);
            URL.revokeObjectURL(audioUrl);
        };

        audio.onerror = (error) => {
            console.error('❌ Audio playback error:', error);
            this.handleAudioError(data.audio_id, error);
            URL.revokeObjectURL(audioUrl);
        };

        // 播放音频
        audio.play().catch(error => {
            console.error('❌ Failed to play audio:', error);
            this.handleAudioError(data.audio_id, error);
            URL.revokeObjectURL(audioUrl);
        });

                    // this.showNotification(`🔊 Playing TTS audio (${Math.round(data.audio_blob.size / 1024)}KB)`); // 移除：TTS播放提示
    }

    /**
     * 播放Base64音频
     * @param {Object} data - 音频数据
     */
    playBase64Audio(data) {
        if (this.audioRecorder) {
            this.audioRecorder.playAudio(data.audio_data, data.format, data.audio_id);
        } else {
            console.warn('AudioRecorder not available for base64 audio playback');
        }
    }

    /**
     * 停止所有音频播放
     */
    stopAllAudio() {
        // 停止AudioRecorder管理的音频
        if (this.audioRecorder) {
            this.audioRecorder.stopAllAudio();
        }

        // 停止当前播放的二进制音频
        if (this.currentAudioElement) {
            this.currentAudioElement.pause();
            this.currentAudioElement = null;
        }

        // 重置状态
        this.isPlaying = false;
        this.currentAudioId = null;
    }

    /**
     * 停止指定音频
     * @param {string} audioId - 音频ID
     */
    stopAudio(audioId) {
        if (this.audioRecorder) {
            this.audioRecorder.stopAudio(audioId);
        }

        if (this.currentAudioId === audioId && this.currentAudioElement) {
            this.currentAudioElement.pause();
            this.currentAudioElement = null;
            this.currentAudioId = null;
            this.isPlaying = false;
        }
    }

    /**
     * 处理音频播放开始
     * @param {string} audioId - 音频ID
     */
    handleAudioPlaying(audioId) {
        this.isPlaying = true;
        this.currentAudioId = audioId;
        this.updatePlaybackUI(audioId, true);
    }

    /**
     * 处理音频播放结束
     * @param {string} audioId - 音频ID
     */
    handleAudioEnded(audioId) {
        this.isPlaying = false;
        this.updatePlaybackUI(audioId, false);
        
        if (this.currentAudioId === audioId) {
            this.currentAudioId = null;
            this.currentAudioElement = null;
        }
    }

    /**
     * 处理音频播放停止
     * @param {string} audioId - 音频ID
     */
    handleAudioStopped(audioId) {
        this.isPlaying = false;
        this.updatePlaybackUI(audioId, false);
        
        if (this.currentAudioId === audioId) {
            this.currentAudioId = null;
            this.currentAudioElement = null;
        }
    }

    /**
     * 处理音频播放错误
     * @param {string} audioId - 音频ID
     * @param {Error} error - 错误对象
     */
    handleAudioError(audioId, error) {
        this.isPlaying = false;
        this.updatePlaybackUI(audioId, false);
        
        if (this.currentAudioId === audioId) {
            this.currentAudioId = null;
            this.currentAudioElement = null;
        }

        this.showNotification('Audio playback failed');
    }

    /**
     * 更新播放UI状态
     * @param {string} audioId - 音频ID
     * @param {boolean} isPlaying - 是否正在播放
     */
    updatePlaybackUI(audioId, isPlaying) {
        // 调用全局的UI更新函数
        if (typeof window.updateAudioPlaybackUI === 'function') {
            window.updateAudioPlaybackUI(audioId, isPlaying);
        }
    }

    /**
     * 显示通知
     * @param {string} message - 通知消息
     */
    showNotification(message) {
        if (typeof window.showNotification === 'function') {
            window.showNotification(message);
        }
    }

    /**
     * 获取当前播放状态
     * @returns {Object} 播放状态信息
     */
    getPlaybackStatus() {
        return {
            isPlaying: this.isPlaying,
            currentAudioId: this.currentAudioId,
            hasCurrentElement: !!this.currentAudioElement
        };
    }

    /**
     * 检查是否正在播放
     * @returns {boolean} 是否正在播放
     */
    isCurrentlyPlaying() {
        return this.isPlaying;
    }

    /**
     * 获取当前播放的音频ID
     * @returns {string|null} 当前音频ID
     */
    getCurrentAudioId() {
        return this.currentAudioId;
    }

    /**
     * 清理资源
     */
    cleanup() {
        this.stopAllAudio();
        this.audioRecorder = null;
        this.currentAudioElement = null;
        this.currentAudioId = null;
        this.isPlaying = false;
    }
}

// 导出类
export { AudioManager }; 