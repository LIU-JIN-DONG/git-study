/**
 * 蓝牙弹窗UI模块
 * 负责渲染和管理蓝牙设备连接弹窗界面
 */

export class BluetoothModalUI {
    constructor(deviceManager) {
        this.deviceManager = deviceManager;
        this.modal = null;
        this.isOpen = false;
        
        // UI元素引用
        this.elements = {};
        
        // 创建弹窗
        this.createModal();
        
        // 绑定设备管理器事件
        this.bindDeviceManagerEvents();
    }
    
    /**
     * 创建弹窗HTML结构
     */
    createModal() {
        // 创建弹窗容器
        this.modal = document.createElement('div');
        this.modal.className = 'bluetooth-modal-overlay hidden';
        this.modal.innerHTML = `
            <div class="bluetooth-modal-container">
                <div class="bluetooth-modal-drag-indicator">
                    <div class="drag-bar"></div>
                </div>
                <div class="bluetooth-modal-header">
                    <h2 class="bluetooth-modal-title">Bluetooth Devices</h2>
                    <button class="bluetooth-modal-close" aria-label="Close">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M15 5L5 15M5 5l10 10"/>
                        </svg>
                    </button>
                </div>
                
                <div class="bluetooth-modal-body">
                    <!-- 连接状态标题 -->
                    <div class="bluetooth-connection-status" id="connectionStatus"></div>
                    
                    <!-- 已连接设备区域 -->
                    <div class="bluetooth-connected-section" id="connectedSection">
                        <h3 class="bluetooth-section-title">Connected</h3>
                        <div class="bluetooth-connected-devices" id="connectedDevices">
                            <!-- 已连接设备将在这里显示 -->
                        </div>
                    </div>
                    
                    <!-- 可用设备区域 -->
                    <div class="bluetooth-available-section" id="availableSection">
                        <h3 class="bluetooth-section-title">Available Devices</h3>
                        <div class="bluetooth-available-devices" id="availableDevices">
                            <!-- 可用设备将在这里显示 -->
                        </div>
                    </div>
                    
                    <!-- 扫描按钮 -->
                    <button class="bluetooth-scan-button" id="scanButton">
                        <svg class="scan-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 7V4h3M16 7V4h-3M4 13v3h3M16 13v3h-3"/>
                        </svg>
                        <span>Scan for Devices</span>
                    </button>
                </div>
            </div>
        `;
        
        // 添加到手机容器内
        const phoneContainer = document.querySelector('.w-96.h-\\[850px\\]');
        if (phoneContainer) {
            phoneContainer.appendChild(this.modal);
        } else {
            document.body.appendChild(this.modal);
        }
        
        // 获取元素引用
        this.elements = {
            overlay: this.modal,
            container: this.modal.querySelector('.bluetooth-modal-container'),
            closeButton: this.modal.querySelector('.bluetooth-modal-close'),
            connectionStatus: this.modal.querySelector('#connectionStatus'),
            connectedSection: this.modal.querySelector('#connectedSection'),
            connectedDevices: this.modal.querySelector('#connectedDevices'),
            availableSection: this.modal.querySelector('#availableSection'),
            availableDevices: this.modal.querySelector('#availableDevices'),
            scanButton: this.modal.querySelector('#scanButton')
        };
        
        // 绑定UI事件
        this.bindUIEvents();
        
        // 添加样式
        this.injectStyles();
    }
    
    /**
     * 注入CSS样式
     */
    injectStyles() {
        const styleId = 'bluetooth-modal-styles';
        if (document.getElementById(styleId)) return;
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            /* 弹窗遮罩层 */
            .bluetooth-modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.4);
                display: flex;
                align-items: flex-end;
                justify-content: center;
                z-index: 100;
                transition: opacity 0.3s ease;
                border-radius: 48px;
            }
            
            .bluetooth-modal-overlay.hidden {
                display: none;
            }
            
            /* 弹窗容器 */
            .bluetooth-modal-container {
                background: white;
                border-radius: 20px 20px 0 0;
                width: 100%;
                max-height: 500px;
                box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.15);
                overflow: hidden;
                transform: translateY(100%);
                transition: transform 0.3s ease-out;
                margin: 0;
                margin-bottom: 0;
            }
            
            .bluetooth-modal-overlay:not(.hidden) .bluetooth-modal-container {
                transform: translateY(0);
            }
            
            /* 拖拽指示器 */
            .bluetooth-modal-drag-indicator {
                padding: 8px 0 4px 0;
                display: flex;
                justify-content: center;
            }
            
            .drag-bar {
                width: 36px;
                height: 4px;
                background: #d1d5db;
                border-radius: 2px;
            }
            
            @keyframes modalSlideIn {
                from {
                    transform: translateY(100%);
                }
                to {
                    transform: translateY(0);
                }
            }
            
            /* 弹窗头部 */
            .bluetooth-modal-header {
                padding: 12px 24px 20px 24px;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .bluetooth-modal-title {
                font-size: 20px;
                font-weight: 600;
                margin: 0;
                background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .bluetooth-modal-close {
                background: none;
                border: none;
                cursor: pointer;
                padding: 8px;
                border-radius: 8px;
                transition: background 0.2s;
                color: #6b7280;
            }
            
            .bluetooth-modal-close:hover {
                background: #f3f4f6;
            }
            
            /* 弹窗主体 */
            .bluetooth-modal-body {
                padding: 20px 24px 24px 24px;
                max-height: 420px;
                overflow-y: auto;
            }
            
            /* 连接状态 */
            .bluetooth-connection-status {
                font-size: 14px;
                color: #6b7280;
                margin-bottom: 16px;
                min-height: 20px;
            }
            
            .bluetooth-connection-status.connecting {
                color: #3b82f6;
            }
            
            .bluetooth-connection-status.connected {
                color: #10b981;
            }
            
            /* 分区标题 */
            .bluetooth-section-title {
                font-size: 14px;
                font-weight: 500;
                color: #9ca3af;
                margin: 0 0 12px 0;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* 设备列表 */
            .bluetooth-connected-devices,
            .bluetooth-available-devices {
                margin-bottom: 20px;
            }
            
            /* 设备卡片 */
            .bluetooth-device-card {
                background: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 12px;
                cursor: pointer;
                transition: all 0.2s;
                position: relative;
            }
            
            .bluetooth-device-card:hover {
                border-color: #3b82f6;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            
            .bluetooth-device-card.connected {
                background: #ecfdf5;
                border-color: #10b981;
            }
            
            .bluetooth-device-card.connecting {
                opacity: 0.7;
                cursor: not-allowed;
            }
            
            /* 设备状态指示器 */
            .device-status-indicator {
                position: absolute;
                top: 16px;
                right: 16px;
                width: 8px;
                height: 8px;
                border-radius: 50%;
            }
            
            .device-status-indicator.available {
                background: #3b82f6;
            }
            
            .device-status-indicator.connected {
                background: #10b981;
            }
            
            /* 设备信息 */
            .device-name {
                font-size: 16px;
                font-weight: 500;
                color: #1f2937;
                margin-bottom: 4px;
            }
            
            .device-details {
                font-size: 13px;
                color: #6b7280;
            }
            
            .device-battery {
                color: #10b981;
            }
            
            /* 断开按钮 */
            .device-disconnect {
                position: absolute;
                top: 12px;
                right: 12px;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .device-disconnect:hover {
                background: #fee2e2;
                border-color: #ef4444;
                color: #ef4444;
            }
            
            /* 扫描按钮 */
            .bluetooth-scan-button {
                width: 100%;
                padding: 16px;
                background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                transition: all 0.2s;
            }
            
            .bluetooth-scan-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3);
            }
            
            .bluetooth-scan-button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }
            
            .bluetooth-scan-button.scanning .scan-icon {
                animation: spin 2s linear infinite;
            }
            
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            
            /* 滚动条样式 - 移动端优化 */
            .bluetooth-modal-body::-webkit-scrollbar {
                width: 4px;
            }
            
            .bluetooth-modal-body::-webkit-scrollbar-track {
                background: transparent;
            }
            
            .bluetooth-modal-body::-webkit-scrollbar-thumb {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
            }
            
            .bluetooth-modal-body::-webkit-scrollbar-thumb:hover {
                background: rgba(0, 0, 0, 0.3);
            }
            
            /* 移动端滚动优化 */
            .bluetooth-modal-body {
                -webkit-overflow-scrolling: touch;
                overscroll-behavior: contain;
            }
            
            /* 设备列表最多显示2个的滚动容器 */
            .bluetooth-connected-devices {
                max-height: 200px;
                overflow-y: auto;
            }
            
            /* 空状态提示 */
            .empty-state {
                text-align: center;
                color: #9ca3af;
                padding: 20px;
                font-size: 14px;
            }
            
            /* 移动端适配 - 去掉遮罩层圆角 */
            @media only screen and (max-width: 768px) {
                .bluetooth-modal-overlay {
                    border-radius: 0 !important;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    /**
     * 绑定UI事件
     */
    bindUIEvents() {
        // 关闭按钮
        this.elements.closeButton.addEventListener('click', () => this.close());
        
        // 点击遮罩层关闭
        this.elements.overlay.addEventListener('click', (e) => {
            if (e.target === this.elements.overlay) {
                this.close();
            }
        });
        
        // 扫描按钮
        this.elements.scanButton.addEventListener('click', () => this.handleScan());
    }
    
    /**
     * 绑定设备管理器事件
     */
    bindDeviceManagerEvents() {
        // 设备列表更新
        this.deviceManager.addEventListener('devicesUpdated', (e) => {
            this.updateDevicesList(e.detail.devices);
        });
        
        // 设备连接中
        this.deviceManager.addEventListener('deviceConnecting', (e) => {
            this.showConnectingStatus(e.detail.deviceName);
            this.updateDeviceCardStatus(e.detail.deviceId, 'connecting');
        });
        
        // 设备连接成功
        this.deviceManager.addEventListener('deviceConnected', async (e) => {
            console.log('🔗 Modal: Device connected event received:', e.detail.deviceName);
            
            this.showConnectedStatus(e.detail.deviceName);
            this.updateDevicesList(this.deviceManager.getDevicesList());
            
            // 确保音频录制器也连接到设备（解决互动问题）
            const { deviceId, deviceName } = e.detail;
            const device = this.deviceManager.devices.get(deviceId)?.device;
            
            if (device && window.audioRecorder) {
                try {
                    console.log('🔗 Modal: Ensuring audio recorder connection to:', deviceName);
                    const success = await window.audioRecorder.connectBluetoothDevice(device);
                    
                    if (success) {
                        console.log('✅ Modal: Audio recorder connected successfully');
                        
                        // 更新蓝牙按钮状态
                        if (window.bluetoothIntegration) {
                            window.bluetoothIntegration.updateBluetoothButton(true, deviceName);
                        }
                        
                        console.log('✅ Modal: Device connected successfully - keeping modal open for user control');
                    } else {
                        console.error('❌ Modal: Audio recorder connection failed');
                    }
                } catch (error) {
                    console.error('❌ Modal: Error connecting audio recorder:', error);
                }
            } else {
                console.warn('⚠️ Modal: Missing device or audioRecorder:', {
                    device: !!device,
                    audioRecorder: !!window.audioRecorder
                });
            }
        });
        
        // 设备连接失败
        this.deviceManager.addEventListener('deviceConnectionFailed', (e) => {
            this.showConnectionError(e.detail.deviceName, e.detail.error);
            this.updateDeviceCardStatus(e.detail.deviceId, 'available');
        });
        
        // 设备断开连接
        this.deviceManager.addEventListener('deviceDisconnected', (e) => {
            this.hideConnectionStatus();
            this.updateDevicesList(this.deviceManager.getDevicesList());
        });
        
        // 电量更新
        this.deviceManager.addEventListener('batteryLevelUpdated', (e) => {
            this.updateDeviceBattery(e.detail.deviceId, e.detail.batteryLevel);
        });
        
        // 扫描状态
        this.deviceManager.addEventListener('scanStarted', () => {
            this.setScanningState(true);
        });
        
        this.deviceManager.addEventListener('scanCompleted', async (e) => {
            console.log('🔍 Modal: Scan completed for new device:', e.detail.newDevice?.name);
            
            this.setScanningState(false);
            
            // 确保新设备的音频录制器连接（解决原生弹窗连接问题）
            if (e.detail.newDevice && window.audioRecorder) {
                const deviceName = e.detail.newDevice.name;
                
                console.log('🔧 Modal: Ensuring audio recorder connection for scanned device:', deviceName);
                
                // 短暂延迟后检查和连接音频录制器
                setTimeout(async () => {
                    try {
                        // 检查音频录制器连接状态
                        if (window.audioRecorder.inputType !== 'bluetooth' || !window.audioRecorder.bleMicrophone?.isConnected) {
                            console.log('🔧 Modal: Audio recorder not connected after scan, connecting manually...');
                            
                            const success = await window.audioRecorder.connectBluetoothDevice(e.detail.newDevice);
                            if (success) {
                                console.log('✅ Modal: Manual audio recorder connection successful after scan');
                                
                                // 更新蓝牙按钮状态
                                if (window.bluetoothIntegration) {
                                    window.bluetoothIntegration.updateBluetoothButton(true, deviceName);
                                }
                            } else {
                                console.error('❌ Modal: Manual audio recorder connection failed after scan');
                            }
                        } else {
                            console.log('✅ Modal: Audio recorder already connected after scan');
                        }
                        
                        console.log('✅ Modal: Scan completed successfully - keeping modal open for user control');
                        
                    } catch (error) {
                        console.error('❌ Modal: Error in scan completion handler:', error);
                        console.log('⚠️ Modal: Scan error occurred - keeping modal open for user control');
                    }
                }, 1000); // 等1秒让设备管理器的连接流程完成
            } else {
                // 没有新设备或audioRecorder不存在，但保持弹窗开启供用户控制
                console.log('⚠️ Modal: No new device found or audio recorder unavailable - keeping modal open');
            }
        });
        
        this.deviceManager.addEventListener('scanFailed', () => {
            this.setScanningState(false);
        });
    }
    
    /**
     * 打开弹窗
     */
    open() {
        if (this.isOpen) return;
        
        this.modal.classList.remove('hidden');
        this.isOpen = true;
        
        // 加载设备列表
        this.deviceManager.loadSavedDevices();
    }
    
    /**
     * 关闭弹窗
     */
    close() {
        if (!this.isOpen) return;
        
        this.modal.classList.add('hidden');
        this.isOpen = false;
    }
    
    /**
     * 更新设备列表
     */
    updateDevicesList(devices) {
        const connectedDevices = devices.filter(d => d.isConnected);
        const availableDevices = devices.filter(d => !d.isConnected);
        
        // 更新已连接设备
        this.updateConnectedDevices(connectedDevices);
        
        // 更新可用设备
        this.updateAvailableDevices(availableDevices);
        
        // 更新区域可见性
        this.elements.connectedSection.style.display = connectedDevices.length > 0 ? 'block' : 'none';
    }
    
    /**
     * 更新已连接设备列表
     */
    updateConnectedDevices(devices) {
        if (devices.length === 0) {
            this.elements.connectedDevices.innerHTML = '';
            return;
        }
        
        this.elements.connectedDevices.innerHTML = devices.map(device => `
            <div class="bluetooth-device-card connected" data-device-id="${device.id}">
                <div class="device-status-indicator connected"></div>
                <div class="device-name">${device.name}</div>
                <div class="device-details">
                    <span class="device-type">Neural Audio</span>
                    ${device.batteryLevel !== null ? `<span class="device-battery">• ${device.batteryLevel}% Battery</span>` : ''}
                </div>
                <button class="device-disconnect" data-device-id="${device.id}" aria-label="Disconnect">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 4L4 12M4 4l8 8"/>
                    </svg>
                </button>
            </div>
        `).join('');
        
        // 绑定断开连接按钮事件
        this.elements.connectedDevices.querySelectorAll('.device-disconnect').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const deviceId = btn.getAttribute('data-device-id');
                this.deviceManager.disconnectDevice(deviceId);
            });
        });
    }
    
    /**
     * 更新可用设备列表
     */
    updateAvailableDevices(devices) {
        if (devices.length === 0) {
            this.elements.availableDevices.innerHTML = '<div class="empty-state">No available devices</div>';
            return;
        }
        
        this.elements.availableDevices.innerHTML = devices.map(device => `
            <div class="bluetooth-device-card" data-device-id="${device.id}">
                <div class="device-status-indicator available"></div>
                <div class="device-name">${device.name}</div>
            </div>
        `).join('');
        
        // 绑定连接事件
        this.elements.availableDevices.querySelectorAll('.bluetooth-device-card').forEach(card => {
            card.addEventListener('click', () => {
                const deviceId = card.getAttribute('data-device-id');
                this.deviceManager.connectDevice(deviceId);
            });
        });
    }
    
    /**
     * 显示连接中状态
     */
    showConnectingStatus(deviceName) {
        this.elements.connectionStatus.textContent = `Connecting to ${deviceName}...`;
        this.elements.connectionStatus.className = 'bluetooth-connection-status connecting';
    }
    
    /**
     * 显示已连接状态
     */
    showConnectedStatus(deviceName) {
        this.elements.connectionStatus.textContent = `Connected to ${deviceName}`;
        this.elements.connectionStatus.className = 'bluetooth-connection-status connected';
        
        // 3秒后清除状态
        setTimeout(() => {
            this.hideConnectionStatus();
        }, 3000);
    }
    
    /**
     * 显示连接错误
     */
    showConnectionError(deviceName, error) {
        this.elements.connectionStatus.textContent = `Failed to connect to ${deviceName}`;
        this.elements.connectionStatus.className = 'bluetooth-connection-status error';
        
        // 3秒后清除状态
        setTimeout(() => {
            this.hideConnectionStatus();
        }, 3000);
    }
    
    /**
     * 隐藏连接状态
     */
    hideConnectionStatus() {
        this.elements.connectionStatus.textContent = '';
        this.elements.connectionStatus.className = 'bluetooth-connection-status';
    }
    
    /**
     * 更新设备卡片状态
     */
    updateDeviceCardStatus(deviceId, status) {
        const card = this.modal.querySelector(`.bluetooth-device-card[data-device-id="${deviceId}"]`);
        if (!card) return;
        
        card.className = `bluetooth-device-card ${status}`;
    }
    
    /**
     * 更新设备电量
     */
    updateDeviceBattery(deviceId, batteryLevel) {
        const card = this.modal.querySelector(`.bluetooth-device-card[data-device-id="${deviceId}"] .device-battery`);
        if (card) {
            card.textContent = `• ${batteryLevel}% Battery`;
        }
    }
    
    /**
     * 处理扫描
     */
    async handleScan() {
        try {
            // 使用项目特定的过滤器
            await this.deviceManager.scanForDevices([
                { namePrefix: "HA-" },
                { services: ['0000181c-0000-1000-8000-00805f9b34fb'] }
            ]);
        } catch (error) {
            console.error('Scan failed:', error);
        }
    }
    
    /**
     * 设置扫描状态
     */
    setScanningState(isScanning) {
        this.elements.scanButton.disabled = isScanning;
        this.elements.scanButton.classList.toggle('scanning', isScanning);
        
        if (isScanning) {
            this.elements.scanButton.querySelector('span').textContent = 'Scanning...';
        } else {
            this.elements.scanButton.querySelector('span').textContent = 'Scan for Devices';
        }
    }
    
    /**
     * 清理资源
     */
    destroy() {
        if (this.modal) {
            this.modal.remove();
        }
    }
}
