/**
 * AI状态指示器组件
 * 管理AI神经网络状态显示和动画效果
 */
class AIStatusIndicator {
    constructor() {
        this.aiStatusElement = null;
        this.languageStatusElement = null;
        this.neuralDotsContainer = null;
        this.isAnimating = false;
        this.currentStatus = 'inactive';
        
        this.init();
    }

    init() {
        this.createStyles();
        this.bindElements();
    }

    createStyles() {
        const styleId = 'ai-status-indicator-styles';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            /* Neural wave animation for AI status dots */
            .neural-dots-container {
                display: flex;
                gap: 4px;
                align-items: center;
            }

            .neural-dot {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                transition: all 0.3s ease;
            }

            .neural-dot.blue { background-color: #3b82f6; }
            .neural-dot.purple { background-color: #8b5cf6; }
            .neural-dot.pink { background-color: #ec4899; }

            .neural-dot.animate {
                animation: neural-wave 2s ease-in-out infinite;
            }

            .neural-dot.animate:nth-child(2) {
                animation-delay: 0.2s;
            }

            .neural-dot.animate:nth-child(3) {
                animation-delay: 0.4s;
            }

            @keyframes neural-wave {
                0%, 100% { 
                    transform: translateY(0px) scale(1);
                    opacity: 0.7;
                }
                25% { 
                    transform: translateY(-4px) scale(1.1);
                    opacity: 0.9;
                }
                50% { 
                    transform: translateY(-8px) scale(1.2);
                    opacity: 1;
                }
                75% { 
                    transform: translateY(-4px) scale(1.1);
                    opacity: 0.9;
                }
            }

            /* 状态指示器容器样式 */
            .ai-status-container {
                padding: 12px;
                background: rgba(255, 255, 255, 0.8);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                border: 1px solid rgba(59, 130, 246, 0.2);
                transition: all 0.3s ease;
            }

            .ai-status-container.active {
                border-color: rgba(59, 130, 246, 0.4);
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
            }

            .ai-status-text {
                font-size: 12px;
                font-weight: 500;
                color: #374151;
                margin: 0;
                text-align: center;
            }

            .ai-status-detail {
                font-size: 11px;
                color: #6b7280;
                margin: 2px 0 0 0;
                text-align: center;
            }
        `;
        document.head.appendChild(style);
    }

    bindElements() {
        this.aiStatusElement = document.getElementById('aiStatus');
        this.languageStatusElement = document.getElementById('languageStatus');
        this.neuralDotsContainer = document.querySelector('.neural-dots-container');
        
        if (!this.neuralDotsContainer) {
            console.warn('Neural dots container not found');
        }
    }

    // 开始动画
    startAnimation() {
        if (this.isAnimating) return;
        
        this.isAnimating = true;
        const dots = document.querySelectorAll('.neural-dot');
        dots.forEach(dot => {
            dot.classList.add('animate');
        });

        const container = document.querySelector('.ai-status-container');
        if (container) {
            container.classList.add('active');
        }
    }

    // 停止动画
    stopAnimation() {
        if (!this.isAnimating) return;
        
        this.isAnimating = false;
        const dots = document.querySelectorAll('.neural-dot');
        dots.forEach(dot => {
            dot.classList.remove('animate');
        });

        const container = document.querySelector('.ai-status-container');
        if (container) {
            container.classList.remove('active');
        }
    }

    // 更新状态
    updateStatus(status, detail = '') {
        if (this.aiStatusElement) {
            this.aiStatusElement.textContent = status;
        }
        
        if (this.languageStatusElement && detail) {
            this.languageStatusElement.textContent = detail;
        }

        this.currentStatus = status;
        
        // 根据状态决定是否显示动画
        this.handleStatusChange(status);
    }

    // 处理状态变化
    handleStatusChange(status) {
        const animationStates = [
            'Initializing neural pathways...',
            'Calibrating voice recognition...',
            'AI Neural Network Online',
            'Neural network processing...',
            'Switching language...'
        ];

        if (animationStates.includes(status)) {
            this.startAnimation();
        } else {
            this.stopAnimation();
        }
    }

    // AI神经网络初始化序列
    startInitializationSequence() {
        const initSteps = [
            { status: 'Initializing neural pathways...', detail: 'Loading language models', delay: 800 },
            { status: 'Calibrating voice recognition...', detail: 'Optimizing microphone arrays', delay: 1600 },
            { status: 'AI Neural Network Online', detail: 'Ready for intelligent translation', delay: 2400, complete: true }
        ];

        initSteps.forEach((step, index) => {
            setTimeout(() => {
                this.updateStatus(step.status, step.detail);

                if (step.complete) {
                    // 初始化完成后，延迟停止动画
                    setTimeout(() => {
                        this.updateStatus('AI Neural Network Active', 'Ready for translation');
                    }, 1000);
                }
            }, step.delay);
        });
    }

    // 设置为就绪状态
    setReady() {
        this.updateStatus('AI Neural Network Active', 'Ready for translation');
    }

    // 设置为神经网络处理状态（录音开始到翻译完成）
    setNeuralProcessing() {
        this.updateStatus('Neural network processing...', 'Processing audio and translation');
    }

    // 设置为监听状态（保留兼容性，但内部使用神经网络处理）
    setListening() {
        this.setNeuralProcessing();
    }

    // 设置为处理状态（保留兼容性，但内部使用神经网络处理）
    setProcessing() {
        this.setNeuralProcessing();
    }

    // 设置为完成状态（直接设置为就绪，不显示完成状态）
    setComplete() {
        this.setReady();
    }

    // 设置为播放状态（保持就绪状态）
    setPlaying() {
        this.setReady();
    }

    // 设置为语言切换状态
    setSwitchingLanguage() {
        this.updateStatus('Switching language...', 'Updating translation settings');
        setTimeout(() => {
            this.setReady();
        }, 1500);
    }

    // 设置队列处理状态
    setQueueProcessing(queueLength) {
        this.updateStatus('Neural network processing...', `Processing queue: ${queueLength} items`);
    }

    // 获取当前状态
    getCurrentStatus() {
        return this.currentStatus;
    }

    // 检查是否正在动画
    isCurrentlyAnimating() {
        return this.isAnimating;
    }
}

// 导出类
export { AIStatusIndicator }; 