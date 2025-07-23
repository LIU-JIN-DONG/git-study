/**
 * 蓝牙集成模块
 * 负责连接蓝牙设备管理器和音频录制器
 */

export class BluetoothIntegration {
    constructor(deviceManager, audioRecorder) {
        console.log('🔧 BluetoothIntegration: Initializing with:', {
            deviceManager: !!deviceManager,
            audioRecorder: !!audioRecorder
        });
        
        this.deviceManager = deviceManager;
        this.audioRecorder = audioRecorder;
        
        // 绑定设备管理器事件
        this.bindEvents();
        
        console.log('✅ BluetoothIntegration: Initialization completed');
    }
    
    /**
     * 绑定设备管理器事件
     */
    bindEvents() {
        console.log('🔧 BluetoothIntegration: Binding event listeners to device manager...');
        console.log('🔧 BluetoothIntegration: Device manager instance:', this.deviceManager);
        console.log('🔧 BluetoothIntegration: Audio recorder instance:', this.audioRecorder);
        
        // 设备连接成功
        console.log('🔧 BluetoothIntegration: Adding deviceConnected event listener');
        this.deviceManager.addEventListener('deviceConnected', async (e) => {
            const { deviceId, deviceName } = e.detail;
            const device = this.deviceManager.devices.get(deviceId)?.device;
            
            console.log('🔗 Integration: Processing deviceConnected event for:', deviceName);
            
            if (device && this.audioRecorder) {
                try {
                    console.log('🔗 Integration: Connecting audio recorder to device...');
                    
                    // 使用音频录制器的蓝牙连接功能
                    const success = await this.audioRecorder.connectBluetoothDevice(device);
                    
                    if (success) {
                        console.log('✅ Integration: Audio recorder connected successfully');
                        // this.showNotification(`Connected to ${deviceName}`); // 移除：连接成功提示
                        this.updateBluetoothButton(true, deviceName);
                        
                        // 注意：不要再次调用 registerExternalConnection，因为事件已经来自设备管理器
                        // this.deviceManager.registerExternalConnection(device); // 移除：避免重复处理
                        
                        // 绑定音频录制器的断开事件，用于处理异常断开
                        this.bindAudioRecorderDisconnectEvent(deviceName);
                    } else {
                        console.error('❌ Integration: Audio recorder connection failed');
                    }
                } catch (error) {
                    console.error('❌ Integration: Failed to integrate with audio recorder:', error);
                }
            } else {
                if (!device) console.error('❌ Integration: Device not found in device manager');
                if (!this.audioRecorder) console.error('❌ Integration: Audio recorder not available');
            }
        });
        
        // 设备断开连接 - 由设备管理器触发
        this.deviceManager.addEventListener('deviceDisconnected', async (e) => {
            const { deviceName, unexpected } = e.detail;
            
            console.log('📱 Device manager disconnect event:', { deviceName, unexpected });
            
            // 设置标志，防止 bleDisconnected 事件重复处理
            this.isHandlingDeviceManagerDisconnect = true;
            
            try {
                // 如果音频录制器还在使用蓝牙，切换回系统麦克风
                if (this.audioRecorder && this.audioRecorder.inputType === 'bluetooth') {
                    await this.audioRecorder.switchToSystem();
                }
                
                // 显示相应的断开提示
                if (unexpected) {
                    this.showNotification(`${deviceName} disconnected unexpectedly`);
                } else {
                    this.showNotification(`Disconnected from ${deviceName}`);
                }
                
                this.updateBluetoothButton(false);
                
            } catch (error) {
                console.error('Failed to switch audio input:', error);
                // 即使切换失败，也要显示断开提示
                this.showNotification(`${deviceName} disconnected`);
                this.updateBluetoothButton(false);
            } finally {
                // 清除标志
                setTimeout(() => {
                    this.isHandlingDeviceManagerDisconnect = false;
                }, 1000);
            }
        });
        
        // 设备连接失败
        this.deviceManager.addEventListener('deviceConnectionFailed', (e) => {
            const { deviceName, error } = e.detail;
            // this.showNotification(`Failed to connect to ${deviceName}: ${error}`); // 移除：连接失败提示
        });
    }
    
    /**
     * 显示通知
     */
    showNotification(message) {
        // 使用全局的showNotification函数
        if (typeof window.showNotification === 'function') {
            window.showNotification(message);
        } else {
            console.log(message);
        }
    }
    
    /**
     * 更新蓝牙按钮状态
     */
    updateBluetoothButton(connected, deviceName = '') {
        const bluetoothBtn = document.getElementById('bluetoothBtn');
        if (bluetoothBtn) {
            if (connected) {
                bluetoothBtn.title = `Connected to ${deviceName}`;
                bluetoothBtn.classList.add('connected');
            } else {
                bluetoothBtn.title = 'Connect BLE Microphone';
                bluetoothBtn.classList.remove('connected');
            }
        }
    }
    
    /**
     * 获取当前连接状态
     */
    isConnected() {
        return this.audioRecorder?.inputType === 'bluetooth';
    }
    
    /**
     * 获取当前连接的设备信息
     */
    getConnectedDevice() {
        if (this.isConnected()) {
            return this.deviceManager.getConnectedDevice();
        }
        return null;
    }
    
    /**
     * 绑定音频录制器断开事件（用于处理异常断开）
     */
    bindAudioRecorderDisconnectEvent(deviceName) {
        // 清除之前的监听器
        if (this.bleDisconnectHandler) {
            this.audioRecorder.off('bleDisconnected', this.bleDisconnectHandler);
        }
        
        // 设置新的断开事件处理器
        this.bleDisconnectHandler = () => {
            console.log('🔴 BLE device disconnected via audio recorder');
            
            // 如果设备管理器正在处理断开事件，则跳过
            if (this.isHandlingDeviceManagerDisconnect) {
                console.log('⏭️ Skipping BLE disconnect handler - already handled by device manager');
                return;
            }
            
            // 如果没有被设备管理器处理，说明是通过其他方式断开的
            console.log('📱 Showing fallback BLE disconnect notification');
            this.showNotification('BLE Microphone disconnected');
            this.updateBluetoothButton(false);
        };
        
        // 绑定事件监听器
        this.audioRecorder.on('bleDisconnected', this.bleDisconnectHandler);
        console.log('🔗 Bound BLE disconnect handler for:', deviceName);
    }
    
    /**
     * 清理资源
     */
    destroy() {
        // 清除事件监听器
        if (this.bleDisconnectHandler && this.audioRecorder) {
            this.audioRecorder.off('bleDisconnected', this.bleDisconnectHandler);
            this.bleDisconnectHandler = null;
        }
    }
}

// 创建并导出集成实例（需要在主文件中初始化）
export let bluetoothIntegration = null;

export function initializeBluetoothIntegration(deviceManager, audioRecorder) {
    bluetoothIntegration = new BluetoothIntegration(deviceManager, audioRecorder);
    return bluetoothIntegration;
}
