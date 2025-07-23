/**
 * 转录状态指示器管理器
 * 负责管理转录过程中的状态指示器显示和隐藏
 */
export class TranscriptionIndicator {
    constructor() {
        this.isActive = false;
        this.indicatorElement = null;
        this.svgPath = 'static/js/picture/旋转转录.svg';
        this.containerId = 'transcriptionIndicator';
        
        this.init();
    }

    /**
     * 初始化指示器
     */
    init() {
        this.createIndicatorElement();
        this.setupStyles();
    }

    /**
     * 创建指示器元素
     */
    createIndicatorElement() {
        // 创建指示器容器
        this.indicatorElement = document.createElement('div');
        this.indicatorElement.id = this.containerId;
        this.indicatorElement.className = 'transcription-indicator hidden';
        
        // 创建SVG图标
        this.indicatorElement.innerHTML = `
            <div class="transcription-icon">
                <img src="${this.svgPath}" alt="转录中" width="24" height="24">
            </div>
        `;
        
        // 找到下方输入框（转录区域）的右上角容器
        const transcriptionBox = document.querySelector('#transcriptionContent').closest('.relative');
        const rightTopContainer = transcriptionBox ? transcriptionBox.querySelector('.absolute.top-3.right-3') : null;
        
        if (rightTopContainer) {
            rightTopContainer.appendChild(this.indicatorElement);
        } else {
            console.error('❌ 未找到下方输入框右上角容器，无法添加转录指示器');
        }
    }

    /**
     * 设置样式
     */
    setupStyles() {
        // 检查是否已经有样式
        if (document.getElementById('transcription-indicator-styles')) {
            return;
        }

        const style = document.createElement('style');
        style.id = 'transcription-indicator-styles';
        style.textContent = `
            .transcription-indicator {
                position: relative;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-left: 8px;
                transition: opacity 0.3s ease;
            }

            .transcription-indicator.hidden {
                opacity: 0;
                pointer-events: none;
            }

            .transcription-indicator.visible {
                opacity: 1;
                pointer-events: auto;
            }

            .transcription-icon {
                display: flex;
                align-items: center;
                justify-content: center;
                animation: spin 1s linear infinite;
            }

            .transcription-icon img {
                width: 24px;
                height: 24px;
                opacity: 0.8;
            }

            @keyframes spin {
                from {
                    transform: rotate(0deg);
                }
                to {
                    transform: rotate(360deg);
                }
            }


        `;
        
        document.head.appendChild(style);
    }

    /**
     * 显示转录指示器
     */
    show() {
        if (!this.indicatorElement) {
            console.error('❌ 转录指示器元素未找到');
            return;
        }

        this.isActive = true;
        this.indicatorElement.classList.remove('hidden');
        this.indicatorElement.classList.add('visible');
        
        console.log('🔄 转录指示器显示');
    }

    /**
     * 隐藏转录指示器
     */
    hide() {
        if (!this.indicatorElement) {
            console.error('❌ 转录指示器元素未找到');
            return;
        }

        this.isActive = false;
        this.indicatorElement.classList.remove('visible');
        this.indicatorElement.classList.add('hidden');
        
        console.log('✅ 转录指示器隐藏');
    }

    /**
     * 切换转录指示器状态
     */
    toggle() {
        if (this.isActive) {
            this.hide();
        } else {
            this.show();
        }
    }

    /**
     * 获取当前状态
     */
    getState() {
        return {
            isActive: this.isActive,
            elementExists: !!this.indicatorElement
        };
    }

    /**
     * 销毁指示器
     */
    destroy() {
        if (this.indicatorElement) {
            this.indicatorElement.remove();
            this.indicatorElement = null;
        }
        
        // 移除样式
        const styleElement = document.getElementById('transcription-indicator-styles');
        if (styleElement) {
            styleElement.remove();
        }
        
        this.isActive = false;
        console.log('🗑️ 转录指示器已销毁');
    }
} 