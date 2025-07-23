/**
 * 翻译状态指示器管理器
 * 负责管理翻译过程中的状态指示器显示和隐藏
 */
export class TranslationIndicator {
    constructor() {
        this.isActive = false;
        this.indicatorElement = null;
        this.svgPath = 'static/js/picture/正在翻译.svg';
        this.containerId = 'translationIndicator';
        
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
        this.indicatorElement.className = 'translation-indicator hidden';
        
        // 创建SVG图标
        this.indicatorElement.innerHTML = `
            <div class="translation-icon">
                <img src="${this.svgPath}" alt="翻译中" width="24" height="24">
            </div>
        `;
        
        // 找到上方输出框（翻译区域）的右上角容器
        const translationBox = document.querySelector('#translationContent').closest('.relative');
        const rightTopContainer = translationBox ? translationBox.querySelector('.absolute.top-3.right-3') : null;
        
        if (rightTopContainer) {
            rightTopContainer.appendChild(this.indicatorElement);
        } else {
            console.error('❌ 未找到上方输出框右上角容器，无法添加翻译指示器');
        }
    }

    /**
     * 设置样式
     */
    setupStyles() {
        // 检查是否已经有样式
        if (document.getElementById('translation-indicator-styles')) {
            return;
        }

        const style = document.createElement('style');
        style.id = 'translation-indicator-styles';
        style.textContent = `
            .translation-indicator {
                position: relative;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-left: 8px;
                transition: opacity 0.3s ease;
            }

            .translation-indicator.hidden {
                opacity: 0;
                pointer-events: none;
            }

            .translation-indicator.visible {
                opacity: 1;
                pointer-events: auto;
            }

            .translation-icon {
                display: flex;
                align-items: center;
                justify-content: center;
                animation: blink 1.5s ease-in-out infinite;
            }

            .translation-icon img {
                width: 24px;
                height: 24px;
                opacity: 0.8;
            }

            @keyframes blink {
                0%, 50% {
                    opacity: 1;
                }
                51%, 100% {
                    opacity: 0.3;
                }
            }
        `;
        
        document.head.appendChild(style);
    }

    /**
     * 显示翻译指示器
     */
    show() {
        if (!this.indicatorElement) {
            console.error('❌ 翻译指示器元素未找到');
            return;
        }

        this.isActive = true;
        this.indicatorElement.classList.remove('hidden');
        this.indicatorElement.classList.add('visible');
        
        console.log('✨ 翻译指示器显示');
    }

    /**
     * 隐藏翻译指示器
     */
    hide() {
        if (!this.indicatorElement) {
            console.error('❌ 翻译指示器元素未找到');
            return;
        }

        this.isActive = false;
        this.indicatorElement.classList.remove('visible');
        this.indicatorElement.classList.add('hidden');
        
        console.log('✅ 翻译指示器隐藏');
    }

    /**
     * 切换翻译指示器状态
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
        const styleElement = document.getElementById('translation-indicator-styles');
        if (styleElement) {
            styleElement.remove();
        }
        
        this.isActive = false;
        console.log('🗑️ 翻译指示器已销毁');
    }
} 