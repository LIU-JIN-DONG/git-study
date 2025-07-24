/**
 * 历史记录管理器组件
 * 负责处理对话历史记录的显示、隐藏、数据加载和HTML生成
 */

export class HistoryManager {
    constructor() {
        this.isExpanded = false;
        this.currentSessionId = null;
        this.wsClient = null;
        this.apiClient = null;
        
        // 绑定DOM元素
        this.elements = {
            historyBox: null,
            historyContent: null,
            historyHintText: null,
            historyHintIcon: null,
            mainInterface: null,
            recordingControls: null
        };
        
        // 容器尺寸配置
        this.containerConfig = {
            totalHeight: 850,
            headerHeight: 100,
            aiStatusHeight: 80,
            historyToggleHeight: 40,
            padding: 60
        };
    }

    /**
     * 初始化历史记录管理器
     * @param {Object} options 初始化选项
     */
    init(options = {}) {
        // 设置配置
        if (options.containerConfig) {
            this.containerConfig = { ...this.containerConfig, ...options.containerConfig };
        }
        
        // 绑定DOM元素
        this.bindElements();
        
        // 设置事件监听器
        this.setupEventListeners();
        
        console.log('HistoryManager initialized');
    }

    /**
     * 绑定DOM元素
     */
    bindElements() {
        this.elements.historyBox = document.getElementById('historyBox');
        this.elements.historyContent = document.getElementById('historyContent');
        this.elements.historyHintText = document.getElementById('historyHintText');
        this.elements.historyHintIcon = document.getElementById('historyHintIcon');
        this.elements.mainInterface = document.getElementById('mainTranslationInterface');
        this.elements.recordingControls = document.getElementById('recordingControls');
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 监听模块准备就绪事件
        window.addEventListener('modulesReady', () => {
            this.loadHistoryData();
        });
    }

    /**
     * 设置WebSocket客户端引用
     * @param {Object} wsClient WebSocket客户端实例
     * @param {String} sessionId 当前会话ID
     */
    setWebSocketClient(wsClient, sessionId) {
        this.wsClient = wsClient;
        this.currentSessionId = sessionId;
    }

    /**
     * 设置API客户端
     * @param {Object} apiClient API客户端实例
     */
    setAPIClient(apiClient) {
        this.apiClient = apiClient;
    }

    /**
     * 切换历史记录展示状态
     */
    toggle() {
        this.isExpanded = !this.isExpanded;
        
        if (this.isExpanded) {
            this.show();
        } else {
            this.hide();
        }
    }

    /**
     * 显示历史记录视图
     */
    show() {
        const { historyBox, mainInterface, recordingControls, historyHintText, historyHintIcon } = this.elements;
        
        // 1. 隐藏主界面和录音按钮
        mainInterface.classList.add('main-interface-hidden');
        recordingControls.classList.add('recording-controls-hidden');
        
        // 2. 计算可用空间
        const availableHeight = this.calculateAvailableHeight();
        document.documentElement.style.setProperty('--history-expanded-height', `${availableHeight}px`);
        
        // 3. 展开历史记录
        historyBox.classList.add('expanded');
        
        // 4. 更新按钮状态
        historyHintText.textContent = 'Hide';
        historyHintIcon.style.transform = 'rotate(180deg)';
        
        // 5. 加载历史记录数据
        setTimeout(() => {
            this.loadHistoryData();
        }, 100); // 稍微延迟加载，等待展开动画
    }

    /**
     * 隐藏历史记录视图
     */
    hide() {
        const { historyBox, mainInterface, recordingControls, historyHintText, historyHintIcon } = this.elements;
        
        // 1. 收起历史记录
        historyBox.classList.remove('expanded');
        
        // 2. 显示主界面和录音按钮
        setTimeout(() => {
            mainInterface.classList.remove('main-interface-hidden');
            recordingControls.classList.remove('recording-controls-hidden');
        }, 200); // 延迟显示，让收起动画先完成
        
        // 3. 重置按钮状态
        historyHintText.textContent = 'History';
        historyHintIcon.style.transform = 'rotate(0deg)';
    }

    /**
     * 计算可用空间高度
     * @returns {number} 可用高度（像素）
     */
    calculateAvailableHeight() {
        const { totalHeight, headerHeight, aiStatusHeight, historyToggleHeight, padding } = this.containerConfig;
        return totalHeight - headerHeight - aiStatusHeight - historyToggleHeight - padding;
    }

    /**
     * 加载历史记录数据
     */
    async loadHistoryData() {
        const { historyContent } = this.elements;
        
        try {
            // 显示加载状态
            historyContent.innerHTML = '<div class="flex justify-center items-center h-20"><div class="text-sm text-gray-500">Loading history...</div></div>';
            
            // 从API获取历史记录
            const historyData = await this.fetchHistoryFromAPI();
            
            // 生成历史记录HTML
            const historyHTML = this.generateHistoryHTML(historyData);
            historyContent.innerHTML = historyHTML;
            
            // 滚动到最新记录
            setTimeout(() => {
                historyContent.scrollTop = historyContent.scrollHeight;
            }, 100);
            
        } catch (error) {
            console.error('加载历史记录失败:', error);
            
            // 显示错误状态
            if (error.message && error.message.includes('HTTP error')) {
                historyContent.innerHTML = this.generateErrorStateHTML('网络连接失败，请检查网络设置');
            } else if (!this.getCurrentSessionId()) {
                historyContent.innerHTML = this.generateErrorStateHTML('未找到会话ID，请重新开始对话');
            } else {
                // 使用模拟数据作为fallback
                const fallbackData = this.generateMockData();
                const historyHTML = this.generateHistoryHTML(fallbackData);
                historyContent.innerHTML = historyHTML;
                
                // 显示警告提示
                this.showWarningMessage('历史记录加载失败，显示模拟数据');
            }
        }
    }

    /**
     * 从API获取历史记录
     * @returns {Promise<Array>} 历史记录数据
     */
    async fetchHistoryFromAPI() {
        try {
            // 获取当前会话ID
            const sessionId = this.getCurrentSessionId();
            
            if (!sessionId) {
                console.warn('没有当前会话ID，使用模拟数据');
                return this.generateMockData();
            }
            
            // 调用API获取历史记录
            const response = await this.apiClient.getHistory(sessionId, 1, 50);
            
            if (response.code === 200 && response.data && response.data.records) {
                return response.data.records;
            } else {
                console.warn('API返回数据格式异常:', response);
                return [];
            }
            
        } catch (error) {
            console.error('API获取历史记录失败:', error);
            throw error;
        }
    }

    /**
     * 获取当前会话ID
     * @returns {string|null} 当前会话ID
     */
    getCurrentSessionId() {
        // 从全局变量获取当前会话ID
        if (typeof window !== 'undefined' && window.currentSessionId) {
            return window.currentSessionId;
        }
        
        // 从WebSocket客户端获取会话ID
        if (this.wsClient && this.wsClient.sessionId) {
            return this.wsClient.sessionId;
        }
        
        return null;
    }

    /**
     * 生成模拟数据
     * @returns {Array} 模拟的对话数据
     */
    generateMockData() {
        return [
            {
                source_text: "嘿！你今天过得怎么样？我希望你一切都顺利。",
                target_text: "Hey there! How's your day going? I hope everything is working out well for you.",
                source_language: "zh-CN",
                target_language: "en-US",
                timestamp: new Date().toISOString()
            },
            {
                source_text: "That's awesome! What kind of work do you do? I'm always curious about different career paths and how people find their passion.",
                target_text: "太棒了！你是做什么工作的？我总是对不同的职业道路以及人们如何找到自己的热情很好奇。",
                source_language: "en-US",
                target_language: "zh-CN",
                timestamp: new Date(Date.now() + 60000).toISOString()
            }
        ];
    }

    /**
     * 生成历史记录HTML
     * @param {Array} conversation 对话数据数组
     * @returns {string} 生成的HTML字符串
     */
    generateHistoryHTML(conversation) {
        if (conversation.length === 0) {
            return this.generateEmptyStateHTML();
        }
        
        let html = '';
        conversation.forEach((item, index) => {
            const time = this.formatTime(item.timestamp);
            const sourceFlag = this.getLanguageFlag(item.source_language);
            const targetFlag = this.getLanguageFlag(item.target_language);
            
            html += `
                <div class="chat-group">
                    <div class="chat-timestamp">${time}</div>
                    
                    <!-- 源语言气泡 - 固定蓝色 -->
                    <div class="chat-bubble p-3 bg-blue-100 border-blue-200">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-sm">${sourceFlag}</span>
                            <span class="text-xs font-medium text-blue-700">${this.getLanguageName(item.source_language)}</span>
                        </div>
                        <div class="text-sm text-gray-800">${item.source_text}</div>
                    </div>
                    
                    <!-- 目标语言气泡 - 固定绿色 -->
                    <div class="chat-bubble p-3 bg-green-100 border-green-200">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-sm">${targetFlag}</span>
                            <span class="text-xs font-medium text-green-700">${this.getLanguageName(item.target_language)}</span>
                        </div>
                        <div class="text-sm text-gray-800">${item.target_text}</div>
                    </div>
                </div>
            `;
        });
        
        return html;
    }

    /**
     * 生成空状态HTML
     * @returns {string} 空状态的HTML
     */
    generateEmptyStateHTML() {
        return `
            <div class="text-center text-gray-400 py-8">
                <svg class="w-12 h-12 mx-auto mb-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/>
                </svg>
                <p class="text-sm">No conversation history yet</p>
                <p class="text-xs text-gray-300 mt-1">Start a conversation to see your translation history</p>
            </div>
        `;
    }

    /**
     * 生成错误状态HTML
     * @param {string} message 错误消息
     * @returns {string} 错误状态HTML
     */
    generateErrorStateHTML(message) {
        return `
            <div class="flex flex-col items-center justify-center h-full text-center py-8">
                <svg class="w-12 h-12 text-red-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <h3 class="text-lg font-medium text-gray-800 mb-2">加载失败</h3>
                <p class="text-sm text-gray-500 mb-4">${message}</p>
                <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors" onclick="historyManager.refreshHistory()">
                    重试
                </button>
            </div>
        `;
    }

    /**
     * 显示警告消息
     * @param {string} message 警告消息
     */
    showWarningMessage(message) {
        // 可以在这里添加通知系统的调用
        console.warn('历史记录管理器警告:', message);
        
        // 如果存在全局通知函数，则调用它
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, 'warning');
        }
    }

    /**
     * 添加新的翻译记录到历史记录
     * @param {Object} translationData 翻译数据
     */
    addTranslation(translationData) {
        // 如果历史记录正在展示，则实时更新
        if (this.isExpanded) {
            this.refreshHistory();
        }
    }

    /**
     * 刷新历史记录
     */
    async refreshHistory() {
        try {
            await this.loadHistoryData();
        } catch (error) {
            console.error('刷新历史记录失败:', error);
        }
    }

    /**
     * 格式化时间戳
     * @param {string} timestamp 时间戳
     * @returns {string} 格式化后的时间
     */
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    }

    /**
     * 获取语言标志
     * @param {string} langCode 语言代码
     * @returns {string} 语言标志SVG图片HTML
     */
    getLanguageFlag(langCode) {
        const flags = {
            'zh-CN': 'static/js/picture/country/中文.svg',
            'en-US': 'static/js/picture/country/English.svg',
            'ja-JP': 'static/js/picture/country/日本語.svg',
            'ko-KR': 'static/js/picture/country/한국어.svg',
            'fr-FR': 'static/js/picture/country/français.svg',
            'de-DE': 'static/js/picture/country/Deutsch.svg',
            'es-ES': 'static/js/picture/country/español.svg',
            'ru-RU': 'static/js/picture/country/русский.svg',
            'ar-SA': 'static/js/picture/country/العربية.svg',
            'vi-VN': 'static/js/picture/country/tiếng Việt.svg',
            'tl-PH': 'static/js/picture/country/Tagalog.svg',
            'it-IT': null,
            'pt-PT': null
        };
        
        const svgPath = flags[langCode];
        if (svgPath) {
            return `<img src="${svgPath}" alt="${langCode}" class="language-flag-svg" />`;
        }
        // 对于没有SVG文件的语言，返回fallback图标
        return `<div class="language-flag-fallback">${langCode.split('-')[0].toUpperCase()}</div>`;
    }

    /**
     * 获取语言名称
     * @param {string} langCode 语言代码
     * @returns {string} 语言名称
     */
    getLanguageName(langCode) {
        const names = {
            'zh-CN': '中文',
            'en-US': 'English',
            'ja-JP': '日本語',
            'ko-KR': '한국어',
            'fr-FR': 'Français',
            'de-DE': 'Deutsch',
            'es-ES': 'Español',
            'ru-RU': 'русский',
            'ar-SA': 'العربية',
            'vi-VN': 'tiếng Việt',
            'tl-PH': 'Tagalog',
            'it-IT': 'Italiano',
            'pt-PT': 'Português'
        };
        return names[langCode] || 'Unknown';
    }

    /**
     * 获取当前展示状态
     * @returns {boolean} 是否展开
     */
    getExpandedState() {
        return this.isExpanded;
    }

    /**
     * 销毁组件
     */
    destroy() {
        // 清理事件监听器和DOM引用
        this.elements = {};
        this.wsClient = null;
        this.currentSessionId = null;
        this.isExpanded = false;
    }
}

// 导出单例实例
export const historyManager = new HistoryManager(); 