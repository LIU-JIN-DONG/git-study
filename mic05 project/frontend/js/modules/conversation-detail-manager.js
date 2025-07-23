/**
 * 会话详情页面管理器
 * 负责管理会话详情页面的显示、数据加载和交互
 */

export class ConversationDetailManager {
    constructor() {
        this.isVisible = false;
        this.currentConversation = null;
        this.currentMessages = [];
        
        // DOM元素引用
        this.elements = {
            detailPage: null,
            conversationsPage: null,
            mainContainer: null,
            backButton: null,
            conversationTitle: null,
            conversationStats: null,
            languageTags: null,
            messagesList: null,
            inputField: null,
            sendButton: null
        };
    }

    /**
     * 初始化模块
     */
    init() {
        this.bindElements();
        this.setupEventListeners();
        console.log('ConversationDetailManager initialized');
    }

    /**
     * 绑定DOM元素
     */
    bindElements() {
        this.elements.detailPage = document.getElementById('conversationDetailPage');
        this.elements.conversationsPage = document.getElementById('conversationsPage');
        this.elements.mainContainer = document.querySelector('body > .relative.w-96.h-\\[850px\\]');
        this.elements.backButton = document.getElementById('detailBackBtn');
        this.elements.conversationTitle = document.getElementById('detailTitle');
        this.elements.conversationStats = document.getElementById('detailStats');
        this.elements.languageTags = document.getElementById('detailLanguageTags');
        this.elements.messagesList = document.getElementById('detailMessages');
        this.elements.inputField = document.getElementById('detailInput');
        this.elements.sendButton = document.getElementById('detailSendBtn');
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        if (this.elements.backButton) {
            this.elements.backButton.addEventListener('click', () => this.hide());
        }

        if (this.elements.sendButton) {
            this.elements.sendButton.addEventListener('click', () => {
                console.log('Send button clicked (placeholder functionality)');
            });
        }
    }

    /**
     * 显示会话详情页面
     */
    async show(conversation) {
        if (!this.elements.detailPage) {
            console.error('Required elements not found');
            return;
        }

        this.currentConversation = conversation;
        this.isVisible = true;
        
        // 隐藏会话列表页面，显示详情页面
        if (this.elements.conversationsPage) {
            this.elements.conversationsPage.classList.add('hidden');
        }
        this.elements.detailPage.classList.remove('hidden');
        
        // 更新页面标题和基本信息
        this.updatePageContent(conversation);
        
        // 从API获取真实消息数据，如果失败则降级到mock数据
        await this.loadConversationMessages(conversation.sessionId);
        
        console.log('Conversation detail page shown for:', conversation.title);
    }

    /**
     * 隐藏详情页面，返回会话列表
     */
    hide() {
        if (this.elements.detailPage && this.elements.conversationsPage) {
            this.elements.detailPage.classList.add('hidden');
            this.elements.conversationsPage.classList.remove('hidden');
            this.isVisible = false;
            console.log('Conversation detail page hidden');
        }
    }

    /**
     * 更新页面内容
     */
    updatePageContent(conversation) {
        const { conversationTitle, conversationStats, languageTags } = this.elements;
        const conv = conversation || this.currentConversation;
        
        if (!conv) return;
        
        // 更新标题
        if (conversationTitle) {
            conversationTitle.textContent = conv.title;
        }
        
        // 更新统计信息
        if (conversationStats) {
            conversationStats.textContent = `${conv.messages} messages • ${conv.duration} • ${this.getRelativeTimeString(conv.timestamp)}`;
        }
        
        // 更新语言标签
        if (languageTags) {
            languageTags.innerHTML = conv.languages.map(lang => this.getLanguageTag(lang)).join('');
        }
    }

    /**
     * 获取语言标签HTML
     * @param {string} langCode 语言代码
     * @returns {string} 语言标签HTML
     */
    getLanguageTag(langCode) {
        const flags = {
            'zh-CN': { svg: 'static/js/picture/country/中文.svg', name: '中' },
            'en-US': { svg: 'static/js/picture/country/English.svg', name: 'EN' },
            'ja-JP': { svg: 'static/js/picture/country/日本語.svg', name: '日本語' },
            'ko-KR': { svg: 'static/js/picture/country/한국어.svg', name: '한国어' },
            'fr-FR': { svg: 'static/js/picture/country/français.svg', name: 'FR' },
            'de-DE': { svg: 'static/js/picture/country/Deutsch.svg', name: 'DE' },
            'es-ES': { svg: 'static/js/picture/country/español.svg', name: 'ES' },
            'ru-RU': { svg: 'static/js/picture/country/русский.svg', name: 'RU' },
            'ar-SA': { svg: 'static/js/picture/country/العربية.svg', name: 'AR' },
            'vi-VN': { svg: 'static/js/picture/country/tiếng Việt.svg', name: 'VI' },
            'tl-PH': { svg: 'static/js/picture/country/Tagalog.svg', name: 'TL' }
        };

        const flag = flags[langCode] || { svg: null, name: langCode };
        
        if (flag.svg) {
            return `
                <div class="flex items-center gap-1 px-2 py-1 rounded-xl border border-blue-200 text-xs" style="background: rgba(59, 130, 246, 0.1);">
                    <img src="${flag.svg}" alt="${flag.name}" class="w-4 h-3">
                    <span class="text-blue-600 font-medium">${flag.name}</span>
                    <span class="text-gray-400">×</span>
                </div>
            `;
        } else {
            return `
                <div class="flex items-center gap-1 px-2 py-1 rounded-xl border border-blue-200 text-xs" style="background: rgba(59, 130, 246, 0.1);">
                    <span class="text-blue-600 font-medium">${flag.name}</span>
                    <span class="text-gray-400">×</span>
                </div>
            `;
        }
    }

    /**
     * 生成消息HTML
     * @returns {string} 消息HTML
     */
    generateMessagesHTML() {
        if (!this.currentMessages || this.currentMessages.length === 0) {
            return '<div class="text-center text-gray-500 py-4">No messages in this conversation</div>';
        }

        let lastTime = null;
        let html = '';
        
        this.currentMessages.forEach((msg, index) => {
            // 如果是新的时间段，添加时间分隔线
            const msgTime = new Date(msg.timestamp);
            const timeStr = msgTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            if (!lastTime || msgTime.getHours() !== lastTime.getHours() || msgTime.getMinutes() !== lastTime.getMinutes()) {
                html += `
                    <div class="flex items-center justify-center my-4">
                        <div class="h-px bg-gray-200 flex-grow"></div>
                        <span class="px-2 text-xs text-gray-500">${timeStr}</span>
                        <div class="h-px bg-gray-200 flex-grow"></div>
                    </div>
                `;
                lastTime = msgTime;
            }
            
            // 消息内容
            html += this.getMessageHTML(msg, index);
        });
        
        return html;
    }

    /**
     * 获取单条消息的HTML
     * @param {Object} msg 消息对象
     * @param {number} index 消息索引
     * @returns {string} 消息HTML
     */
    getMessageHTML(msg, index) {
        const { type, text, language, translation, targetLanguage } = msg;
        const flags = {
            'zh-CN': { svg: 'static/js/picture/country/中文.svg', name: '中文' },
            'en-US': { svg: 'static/js/picture/country/English.svg', name: 'English' },
            'ja-JP': { svg: 'static/js/picture/country/日本語.svg', name: '日本語' },
            'ko-KR': { svg: 'static/js/picture/country/한국어.svg', name: '한국어' },
            'fr-FR': { svg: 'static/js/picture/country/français.svg', name: 'Français' },
            'de-DE': { svg: 'static/js/picture/country/Deutsch.svg', name: 'Deutsch' },
            'es-ES': { svg: 'static/js/picture/country/español.svg', name: 'Español' },
            'ru-RU': { svg: 'static/js/picture/country/русский.svg', name: 'Русский' },
            'ar-SA': { svg: 'static/js/picture/country/العربية.svg', name: 'العربية' },
            'vi-VN': { svg: 'static/js/picture/country/tiếng Việt.svg', name: 'Tiếng Việt' },
            'tl-PH': { svg: 'static/js/picture/country/Tagalog.svg', name: 'Tagalog' }
        };

        const sourceFlag = flags[language] || { svg: null, name: language };
        let html = '';
        
        // 输入消息（蓝色背景）
        html += `
            <div class="mb-4">
                <div class="flex items-center gap-2 mb-1">
                    <img src="${sourceFlag.svg}" alt="${sourceFlag.name}" class="w-4 h-3">
                    <span class="text-xs text-blue-600">${sourceFlag.name}</span>
                </div>
                <div class="bg-blue-100 border border-blue-200 rounded-xl p-3 text-gray-800 text-sm">
                    ${text}
                </div>
            </div>
        `;
        
        // 翻译输出（绿色背景）
        if (translation) {
            const targetFlag = flags[targetLanguage] || { svg: null, name: targetLanguage };
            html += `
                <div class="mb-4">
                    <div class="flex items-center gap-2 mb-1">
                        <img src="${targetFlag.svg}" alt="${targetFlag.name}" class="w-4 h-3">
                        <span class="text-xs text-green-600">${targetFlag.name}</span>
                    </div>
                    <div class="bg-green-100 border border-green-200 rounded-xl p-3 text-gray-800 text-sm">
                        ${translation}
                    </div>
                </div>
            `;
        }
        
        return html;
    }

    /**
     * 从API获取会话消息
     */
    async loadConversationMessages(sessionId) {
        try {
            this.setLoadingState(true);
            
            // 使用全局APIClient获取会话详细消息
            const data = await window.apiClient.getHistory(sessionId, 1, 100);
            
            if (data.code === 200) {
                // 使用真实API数据
                const messages = data.data.records || [];
                const messagesHtml = this.generateMessagesFromAPI(messages);
                this.updateMessagesContainer(messagesHtml);
                console.log('✅ 成功加载真实消息数据:', messages.length, '条消息');
            } else {
                throw new Error(data.message || '获取消息失败');
            }
            
        } catch (error) {
            console.error('❌ API调用失败:', error.message);
            this.showMessageErrorState(error.message);
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * 根据API数据生成消息HTML
     */
    generateMessagesFromAPI(apiMessages) {
        if (!apiMessages || apiMessages.length === 0) {
            return '<div class="text-center text-gray-400 py-8">No messages in this conversation</div>';
        }

        return apiMessages.map((msg, index) => {
            const timestamp = new Date(msg.timestamp);
            const timeString = timestamp.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: false 
            });
            
            // 获取语言标志
            const sourceFlag = this.getLanguageInfo(msg.source_language);
            const targetFlag = this.getLanguageInfo(msg.target_language);

            return `
                <div class="message-group mb-6">
                    <!-- 用户输入 -->
                    <div class="flex justify-end mb-2">
                        <div class="max-w-[80%]">
                            <div class="bg-blue-500 text-white rounded-2xl px-4 py-3 mb-1">
                                <div class="text-sm font-medium">${msg.source_text}</div>
                            </div>
                            <div class="flex items-center justify-end gap-2 text-xs text-gray-400">
                                <div class="flex items-center gap-1">
                                    <img src="${sourceFlag.svg}" alt="${sourceFlag.name}" class="w-3 h-3">
                                    <span>${sourceFlag.name}</span>
                                </div>
                                <span>${timeString}</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- AI翻译响应 -->
                    <div class="flex justify-start">
                        <div class="max-w-[80%]">
                            <div class="bg-gray-100 text-gray-800 rounded-2xl px-4 py-3 mb-1">
                                <div class="text-sm">${msg.target_text}</div>
                            </div>
                            <div class="flex items-center gap-2 text-xs text-gray-400">
                                <div class="flex items-center gap-1">
                                    <img src="${targetFlag.svg}" alt="${targetFlag.name}" class="w-3 h-3">
                                    <span>${targetFlag.name}</span>
                                </div>
                                <span class="text-blue-500">AI Translation</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    /**
     * 获取语言信息（图标和名称）
     */
    getLanguageInfo(langCode) {
        const languageMap = {
            'zh-CN': { svg: 'static/js/picture/country/中文.svg', name: 'Chinese' },
            'en-US': { svg: 'static/js/picture/country/English.svg', name: 'English' },
            'ja-JP': { svg: 'static/js/picture/country/日本語.svg', name: 'Japanese' },
            'ko-KR': { svg: 'static/js/picture/country/한국어.svg', name: 'Korean' },
            'fr-FR': { svg: 'static/js/picture/country/français.svg', name: 'French' },
            'de-DE': { svg: 'static/js/picture/country/Deutsch.svg', name: 'German' },
            'es-ES': { svg: 'static/js/picture/country/español.svg', name: 'Spanish' },
            'ru-RU': { svg: 'static/js/picture/country/русский.svg', name: 'Russian' },
            'ar-SA': { svg: 'static/js/picture/country/العربية.svg', name: 'Arabic' },
            'vi-VN': { svg: 'static/js/picture/country/tiếng Việt.svg', name: 'Vietnamese' },
            'tl-PH': { svg: 'static/js/picture/country/Tagalog.svg', name: 'Tagalog' },
            'Spanish': { svg: 'static/js/picture/country/español.svg', name: 'Spanish' },
            'Russian': { svg: 'static/js/picture/country/русský.svg', name: 'Russian' }
        };

        return languageMap[langCode] || { 
            svg: 'static/js/picture/country/English.svg', 
            name: langCode || 'Unknown' 
        };
    }

    /**
     * 更新消息容器内容
     */
    updateMessagesContainer(messagesHtml) {
        const messagesContainer = this.elements.messagesList;
        if (messagesContainer) {
            messagesContainer.innerHTML = messagesHtml;
            
            // 滚动到底部
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 100);
        }
    }

    /**
     * 设置加载状态
     */
    setLoadingState(isLoading) {
        const messagesContainer = this.elements.messagesList;
        if (messagesContainer && isLoading) {
            messagesContainer.innerHTML = `
                <div class="flex justify-center items-center py-12">
                    <div class="text-gray-400">
                        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-400 mx-auto mb-4"></div>
                        Loading messages...
                    </div>
                </div>
            `;
        }
    }

    /**
     * 显示消息加载错误状态
     */
    showMessageErrorState(errorMessage) {
        const messagesContainer = this.elements.messagesList;
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="flex flex-col justify-center items-center py-12">
                    <div class="text-red-500 mb-4">
                        <svg class="w-10 h-10 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                        </svg>
                        <div class="text-center text-gray-600">
                            <p class="font-medium mb-2">Failed to load messages</p>
                            <p class="text-sm text-gray-500">${errorMessage}</p>
                            <button onclick="window.conversationDetailManager.loadConversationMessages('${this.currentConversation?.sessionId || ''}')" 
                                    class="mt-3 px-3 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors">
                                Retry
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    /**
     * 获取相对时间字符串
     */
    getRelativeTimeString(date) {
        if (!date) return '';
        
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const diffMinutes = Math.floor(diff / 1000 / 60);
        const diffHours = Math.floor(diff / 1000 / 60 / 60);
        const diffDays = Math.floor(diff / 1000 / 60 / 60 / 24);
        
        if (diffMinutes < 1) return 'Just now';
        if (diffMinutes < 60) return `${diffMinutes}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return 'Long time ago';
    }
}

// 导出单例实例
export const conversationDetailManager = new ConversationDetailManager(); 