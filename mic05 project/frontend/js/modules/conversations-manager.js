/**
 * 完整历史记录页面管理器
 * 负责管理 Conversations 页面的显示、搜索、筛选和数据管理
 */

export class ConversationsManager {
    constructor() {
        this.conversations = [];
        this.filteredConversations = [];
        this.currentFilter = 'all';
        this.searchQuery = '';
        this.currentPage = 1;
        this.limit = 20;
        this.total = 0;
        this.isLoading = false;

        // 接口返回的统计数据
        this.apiStats = {
            total: 0,
            messages: 0
        };

        // DOM elements
        this.conversationsContainer = null;
        this.searchInput = null;
        this.filterButtons = null;
        this.statsElements = null;
    }

    async init() {
        this.bindElements();
        this.setupEventListeners();
        // 使用真实API获取数据，如果失败则降级到mock数据
        await this.loadConversations();
    }

    /**
     * 绑定DOM元素
     */
    bindElements() {
        this.conversationsPage = document.getElementById('conversationsPage');
        this.mainContainer = document.querySelector('body > .relative.w-96.h-\\[850px\\]');
        this.searchInput = document.getElementById('conversationsSearch');
        this.filterButtons = document.querySelectorAll('.filter-btn');
        this.conversationsContainer = document.getElementById('conversationsList');
        this.statsElements = {
            sessions: document.getElementById('statsSessions'),
            messages: document.getElementById('statsMessages'),
            avgLength: document.getElementById('statsAvgLength')
        };
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 返回按钮
        const backBtn = document.getElementById('conversationsBackBtn');
        if (backBtn) {
            backBtn.addEventListener('click', () => this.hide());
        }

        // 搜索输入
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.searchQuery = e.target.value.toLowerCase();
                this.filterConversations();
            });
        }

        // 筛选按钮
        this.filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.currentFilter = btn.dataset.filter;
                this.updateFilterButtons();
                this.filterConversations();
            });
        });
    }

    /**
     * 显示页面
     */
    show() {
        if (this.conversationsPage && this.mainContainer) {
            this.conversationsPage.classList.remove('hidden');
            this.mainContainer.classList.add('hidden');
            this.isVisible = true;
            this.updateStats();
            this.renderConversations();
            console.log('Conversations page shown');
        }
    }

    /**
     * 隐藏页面
     */
    hide() {
        if (this.conversationsPage && this.mainContainer) {
            this.conversationsPage.classList.add('hidden');
            this.mainContainer.classList.remove('hidden');
            this.isVisible = false;
            console.log('Conversations page hidden');
        }
    }

    /**
     * 从API获取会话数据
     */
    async loadConversations() {
        try {
            this.setLoadingState(true);

            // 使用全局APIClient获取历史记录
            const data = await window.apiClient.getAllConversations(this.currentPage, this.limit);

            if (data.code === 200) {
                // 转换后端数据格式
                this.conversations = this.transformBackendData(data.data.histories);
                this.total = data.data.total;
                this.filteredConversations = [...this.conversations];

                // 保存接口返回的统计数据
                this.apiStats = {
                    total: data.data.total || 0,
                    messages: data.data.messages || 0
                };

                console.log('✅ 成功加载真实会话数据:', this.conversations.length, '条记录');
                this.updateStats();
                this.renderConversations();
            } else {
                throw new Error(data.message || '获取数据失败');
            }

        } catch (error) {
            console.error('❌ API调用失败:', error.message);
            this.showErrorState(error.message);
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * 转换后端数据为前端格式
     */
    transformBackendData(backendHistories) {
        return backendHistories.map(history => {
            const conversation = history.conversation || [];

            // 提取涉及的语言并去重
            const languagesSet = new Set();
            conversation.forEach(msg => {
                if (msg.source_language) languagesSet.add(msg.source_language);
                if (msg.target_language) languagesSet.add(msg.target_language);
            });
            const languages = Array.from(languagesSet);

            // 计算时长
            const startTime = new Date(history.start_time);
            const endTime = new Date(history.end_time);
            const durationMs = endTime - startTime;
            const durationMinutes = Math.max(1, Math.floor(durationMs / 60000)); // 至少1分钟

            // 生成标题（如果后端没有提供）
            const title = history.title || this.generateDefaultTitle(conversation, languages);

            // 获取最后一条消息
            const lastMessage = conversation.length > 0
                ? conversation[conversation.length - 1].source_text
                : '暂无消息';

            // 提取关键词用于搜索
            const keywords = this.extractKeywords(conversation, title, history.category);

            return {
                id: history.id,
                sessionId: history.session_id, // 保留session_id用于获取详情
                title: title,
                time: this.getRelativeTime(startTime),
                messages: conversation.length,
                duration: `${durationMinutes}m`,
                languages: languages,
                lastMessage: lastMessage,
                participants: 1, // 目前固定为1
                timestamp: startTime,
                keywords: keywords,
                category: history.category || 'Casual',
                summary: history.summary
            };
        });
    }

    /**
     * 生成默认标题
     */
    generateDefaultTitle(conversation, languages) {
        if (conversation.length === 0) return 'Empty Conversation';

        // 基于第一条消息生成标题
        const firstMessage = conversation[0].source_text;
        if (firstMessage.length > 30) {
            return firstMessage.substring(0, 27) + '...';
        }

        // 基于语言生成标题
        if (languages.length >= 2) {
            const langMap = {
                'en-US': 'English',
                'zh-CN': 'Chinese',
                'ja-JP': 'Japanese',
                'ko-KR': 'Korean',
                'es-ES': 'Spanish',
                'fr-FR': 'French',
                'de-DE': 'German',
                'ru-RU': 'Russian',
                'ar-SA': 'Arabic'
            };
            const lang1 = langMap[languages[0]] || languages[0];
            const lang2 = langMap[languages[1]] || languages[1];
            return `${lang1} to ${lang2} Translation`;
        }

        return 'Translation Session';
    }

    /**
     * 提取关键词用于搜索
     */
    extractKeywords(conversation, title, category) {
        const keywords = [];

        // 添加标题关键词
        if (title) {
            keywords.push(...title.toLowerCase().split(/\s+/));
        }

        // 添加分类关键词
        if (category) {
            keywords.push(category.toLowerCase());
        }

        // 从会话内容提取关键词（限制数量避免过多）
        conversation.slice(0, 3).forEach(msg => {
            if (msg.source_text) {
                // 提取英文单词或中文字符
                const words = msg.source_text.match(/[\u4e00-\u9fff]+|[a-zA-Z]+/g) || [];
                keywords.push(...words.map(w => w.toLowerCase()));
            }
        });

        // 去重并限制数量
        return [...new Set(keywords)].slice(0, 10);
    }

    /**
     * 计算相对时间
     */
    getRelativeTime(timestamp) {
        const now = new Date();
        const diff = now - timestamp;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        const weeks = Math.floor(diff / 604800000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        if (weeks < 4) return `${weeks}w ago`;
        return timestamp.toLocaleDateString();
    }

    /**
     * 设置加载状态
     */
    setLoadingState(isLoading) {
        this.isLoading = isLoading;

        if (this.conversationsContainer) {
            if (isLoading) {
                this.conversationsContainer.innerHTML = `
                    <div class="flex justify-center items-center py-12">
                        <div class="text-gray-400">
                            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-400 mx-auto mb-4"></div>
                            Loading conversations...
                        </div>
                    </div>
                `;
            }
        }
    }

    /**
     * 显示错误状态
     */
    showErrorState(errorMessage) {
        if (this.conversationsContainer) {
            this.conversationsContainer.innerHTML = `
                <div class="flex flex-col justify-center items-center py-12">
                    <div class="text-red-500 mb-4">
                        <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                        </svg>
                        <div class="text-center text-gray-600">
                            <p class="font-medium mb-2">Failed to load conversations</p>
                            <p class="text-sm text-gray-500">${errorMessage}</p>
                            <button onclick="window.conversationsManager.loadConversations()" 
                                    class="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
                                Retry
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        // 清空统计数据
        this.conversations = [];
        this.filteredConversations = [];
        this.total = 0;
        this.apiStats = { total: 0, messages: 0 };
        this.updateStats();
    }

    /**
     * 更新筛选按钮状态
     */
    updateFilterButtons() {
        this.filterButtons.forEach(btn => {
            if (btn.dataset.filter === this.currentFilter) {
                btn.classList.add('bg-blue-500', 'text-white');
                btn.classList.remove('bg-gray-100', 'text-gray-700');
            } else {
                btn.classList.remove('bg-blue-500', 'text-white');
                btn.classList.add('bg-gray-100', 'text-gray-700');
            }
        });
    }

    /**
     * 筛选会话
     */
    filterConversations() {
        let filtered = [...this.conversations];

        // 时间筛选
        if (this.currentFilter === 'today') {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            filtered = filtered.filter(conv => conv.timestamp >= today);
        } else if (this.currentFilter === 'this_week') {
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            filtered = filtered.filter(conv => conv.timestamp >= weekAgo);
        }

        // 搜索筛选
        if (this.searchQuery) {
            filtered = filtered.filter(conv =>
                conv.title.toLowerCase().includes(this.searchQuery) ||
                conv.lastMessage.toLowerCase().includes(this.searchQuery) ||
                conv.keywords.some(keyword => keyword.toLowerCase().includes(this.searchQuery))
            );
        }

        this.filteredConversations = filtered;
        this.renderConversations();
        this.updateStats();
    }

    /**
     * 更新统计信息
     */
    updateStats() {
        // 使用接口返回的统计数据
        const totalSessions = this.apiStats.total;
        const totalMessages = this.apiStats.messages;

        // 计算平均时长（仍然使用前端计算，因为接口可能没有提供）
        const totalDuration = this.filteredConversations.reduce((sum, conv) => {
            const duration = parseInt(conv.duration.replace('m', ''));
            return sum + duration;
        }, 0);
        const avgLength = this.filteredConversations.length > 0 ?
            (totalDuration / this.filteredConversations.length).toFixed(1) : 0;

        if (this.statsElements.sessions) {
            this.statsElements.sessions.textContent = totalSessions;
            this.statsElements.sessions.style.background = 'linear-gradient(90deg, rgba(37, 99, 235, 1) 0%, rgba(147, 51, 234, 1) 100%)';
            this.statsElements.sessions.style.backgroundClip = 'text';
            this.statsElements.sessions.style.webkitBackgroundClip = 'text';
            this.statsElements.sessions.style.webkitTextFillColor = 'transparent';
        }
        if (this.statsElements.messages) {
            this.statsElements.messages.textContent = totalMessages;
            this.statsElements.messages.style.background = 'linear-gradient(90deg, rgba(22, 163, 74, 1) 0%, rgba(5, 150, 105, 1) 100%)';
            this.statsElements.messages.style.backgroundClip = 'text';
            this.statsElements.messages.style.webkitBackgroundClip = 'text';
            this.statsElements.messages.style.webkitTextFillColor = 'transparent';
        }
        if (this.statsElements.avgLength) {
            this.statsElements.avgLength.textContent = avgLength;
            this.statsElements.avgLength.style.background = 'linear-gradient(90deg, rgba(147, 51, 234, 1) 0%, rgba(219, 39, 119, 1) 100%)';
            this.statsElements.avgLength.style.backgroundClip = 'text';
            this.statsElements.avgLength.style.webkitBackgroundClip = 'text';
            this.statsElements.avgLength.style.webkitTextFillColor = 'transparent';
        }
    }

    /**
 * 渲染会话列表
 */
    renderConversations() {
        if (!this.conversationsContainer) return;

        const conversationsHTML = this.filteredConversations.map(conv => `
            <div class="conversation-item bg-white/90 backdrop-blur-sm rounded-xl p-4 mb-3 shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer" 
                 data-conversation-id="${conv.id}">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex items-center gap-2">
                        <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <h3 class="font-bold text-gray-800 text-base">${conv.title}</h3>
                    </div>
                    <button class="p-1 hover:bg-gray-100 rounded">
                        <img src="static/js/picture/history/三点菜单.svg" alt="Menu" class="w-4 h-4">
                    </button>
                </div>
                
                <div class="flex items-center gap-3 text-sm text-gray-500 mb-3">
                    <span>${conv.time}</span>
                    <span>•</span>
                    <span>${conv.messages} messages</span>
                    <span>•</span>
                    <span>${conv.duration}</span>
                </div>
                
                <div class="flex items-center gap-2 mb-3 flex-wrap">
                    ${conv.languages.map(lang => this.getLanguageFlag(lang)).join('')}
                </div>
                
                <div class="rounded-xl p-3 mb-3" style="background: linear-gradient(90deg, rgba(249, 250, 251, 1) 0%, rgba(243, 244, 246, 1) 100%);">
                    <div class="text-xs text-gray-500 mb-1">Last message:</div>
                    <div class="text-sm text-gray-700">${conv.lastMessage}</div>
                </div>
                
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2 text-sm text-gray-500">
                        <img src="static/js/picture/history/人物.svg" alt="Participant" class="w-4 h-4">
                        <span>${conv.participants} participant${conv.participants > 1 ? 's' : ''}</span>
                    </div>
                    <img src="static/js/picture/history/详情箭头.svg" alt="Details" class="w-4 h-4">
                </div>
            </div>
        `).join('');

        this.conversationsContainer.innerHTML = conversationsHTML;

        // 添加点击事件
        this.conversationsContainer.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', () => {
                const conversationId = item.dataset.conversationId;
                this.openConversationDetails(conversationId);
            });
        });
    }

    /**
     * 获取语言标识
     */
    getLanguageFlag(langCode) {
        const flags = {
            'zh-CN': { svg: 'static/js/picture/country/中文.svg', name: '中' },
            'en-US': { svg: 'static/js/picture/country/English.svg', name: 'EN' },
            'ja-JP': { svg: 'static/js/picture/country/日本語.svg', name: '日本語' },
            'ko-KR': { svg: 'static/js/picture/country/한국어.svg', name: '한국어' },
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
            return `<div class="flex items-center gap-1 px-2 py-1 rounded-xl border border-blue-200 text-xs" style="background: rgba(59, 130, 246, 0.1);">
                        <img src="${flag.svg}" alt="${flag.name}" class="w-4 h-3">
                        <span class="text-blue-600 font-medium">${flag.name}</span>
                    </div>`;
        } else {
            return `<div class="flex items-center gap-1 px-2 py-1 rounded-xl border border-blue-200 text-xs" style="background: rgba(59, 130, 246, 0.1);">
                        <span class="text-blue-600 font-medium">${flag.name}</span>
                    </div>`;
        }
    }

    /**
     * 打开会话详情
     */
    openConversationDetails(conversationId) {
        console.log('Opening conversation details for ID:', conversationId);

        // 查找对应的会话数据
        const conversation = this.conversations.find(conv => conv.id === parseInt(conversationId));
        if (!conversation) {
            console.error('Conversation not found:', conversationId);
            return;
        }

        // 如果已加载会话详情管理器，则打开详情页面
        if (window.conversationDetailManager) {
            // 传递包含sessionId的完整会话数据
            window.conversationDetailManager.show(conversation);
        } else {
            console.error('ConversationDetailManager not available');
        }
    }

    /**
     * 获取当前可见状态
     */
    isPageVisible() {
        return this.isVisible;
    }
}

// 导出单例实例
export const conversationsManager = new ConversationsManager(); 