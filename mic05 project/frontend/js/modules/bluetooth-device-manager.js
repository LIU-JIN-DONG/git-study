/**
 * 蓝牙设备管理器模块
 * 负责管理蓝牙设备的连接、断开、状态跟踪等功能
 */

export class BluetoothDeviceManager extends EventTarget {
    constructor() {
        super();
        
        // 设备状态管理
        this.devices = new Map(); // 存储所有设备信息
        this.connectedDevice = null; // 当前连接的设备
        this.isScanning = false; // 是否正在扫描
        
        // 初始化
        this.init();
    }
    
    /**
     * 初始化设备管理器
     */
    async init() {
        // 加载已保存的设备
        await this.loadSavedDevices();
    }
    
    /**
     * 加载已授权的设备列表
     */
    async loadSavedDevices() {
        try {
            if (!navigator.bluetooth?.getDevices) {
                console.warn('getDevices API not supported');
                return;
            }
            
            const devices = await navigator.bluetooth.getDevices();
            
            // 清空现有设备列表
            this.devices.clear();
            
            // 添加设备到管理器
            for (const device of devices) {
                this.devices.set(device.id, {
                    device: device,
                    isConnected: false,
                    batteryLevel: null,
                    lastSeen: new Date()
                });
            }
            
            // 触发设备列表更新事件
            this.dispatchEvent(new CustomEvent('devicesUpdated', {
                detail: { devices: this.getDevicesList() }
            }));
            
        } catch (error) {
            console.error('Failed to load saved devices:', error);
        }
    }
    
    /**
     * 获取设备列表（用于UI显示）
     */
    getDevicesList() {
        const devicesList = [];
        
        this.devices.forEach((info, id) => {
            devicesList.push({
                id: id,
                name: info.device.name || 'Unknown Device',
                isConnected: info.isConnected,
                batteryLevel: info.batteryLevel,
                device: info.device
            });
        });
        
        // 排序：已连接的设备排在前面
        return devicesList.sort((a, b) => {
            if (a.isConnected && !b.isConnected) return -1;
            if (!a.isConnected && b.isConnected) return 1;
            return 0;
        });
    }
    
    /**
     * 连接设备
     */
    async connectDevice(deviceId) {
        const deviceInfo = this.devices.get(deviceId);
        if (!deviceInfo) {
            throw new Error('Device not found');
        }
        
        const device = deviceInfo.device;
        
        try {
            // 触发连接中事件
            this.dispatchEvent(new CustomEvent('deviceConnecting', {
                detail: { deviceId, deviceName: device.name }
            }));
            
            // 如果已有连接的设备，先断开
            if (this.connectedDevice && this.connectedDevice !== device) {
                await this.disconnectDevice(this.connectedDevice.id);
            }
            
            // 连接新设备
            const server = await device.gatt.connect();
            
            // 更新设备状态
            deviceInfo.isConnected = true;
            this.connectedDevice = device;
            
            // 尝试获取电量信息
            await this.updateBatteryLevel(device);
            
            // 设置断开连接监听（如果还没有设置）
            this.ensureDisconnectListener(device);
            
            // 触发连接成功事件
            this.dispatchEvent(new CustomEvent('deviceConnected', {
                detail: { 
                    deviceId, 
                    deviceName: device.name,
                    batteryLevel: deviceInfo.batteryLevel
                }
            }));
            
            // 更新设备列表
            this.dispatchEvent(new CustomEvent('devicesUpdated', {
                detail: { devices: this.getDevicesList() }
            }));
            
            return server;
            
        } catch (error) {
            console.error('Failed to connect device:', error);
            
            // 触发连接失败事件
            this.dispatchEvent(new CustomEvent('deviceConnectionFailed', {
                detail: { 
                    deviceId, 
                    deviceName: device.name,
                    error: error.message 
                }
            }));
            
            throw error;
        }
    }
    
    /**
     * 断开设备连接
     */
    async disconnectDevice(deviceId) {
        const deviceInfo = this.devices.get(deviceId);
        if (!deviceInfo || !deviceInfo.isConnected) {
            return;
        }
        
        try {
            const device = deviceInfo.device;
            
            if (device.gatt.connected) {
                device.gatt.disconnect();
            }
            
            // 更新状态
            deviceInfo.isConnected = false;
            deviceInfo.batteryLevel = null;
            
            if (this.connectedDevice === device) {
                this.connectedDevice = null;
            }
            
            // 触发断开事件（主动断开）
            this.dispatchEvent(new CustomEvent('deviceDisconnected', {
                detail: { deviceId, deviceName: device.name, unexpected: false }
            }));
            
            console.log('📡 Dispatched deviceDisconnected event (manual disconnect)');
            
            // 更新设备列表
            this.dispatchEvent(new CustomEvent('devicesUpdated', {
                detail: { devices: this.getDevicesList() }
            }));
            
        } catch (error) {
            console.error('Failed to disconnect device:', error);
        }
    }
    
    /**
     * 处理设备意外断开
     */
    handleDeviceDisconnected(device) {
        console.log('🔴 Device disconnected (GATT server):', device.name);
        
        const deviceId = device.id;
        const deviceInfo = this.devices.get(deviceId);
        
        if (deviceInfo) {
            deviceInfo.isConnected = false;
            deviceInfo.batteryLevel = null;
        }
        
        if (this.connectedDevice === device) {
            this.connectedDevice = null;
        }
        
        // 触发断开事件（标记为意外断开）
        this.dispatchEvent(new CustomEvent('deviceDisconnected', {
            detail: { 
                deviceId, 
                deviceName: device.name,
                unexpected: true 
            }
        }));
        
        console.log('📡 Dispatched deviceDisconnected event (unexpected)');
        
        // 更新设备列表
        this.dispatchEvent(new CustomEvent('devicesUpdated', {
            detail: { devices: this.getDevicesList() }
        }));
    }
    
    /**
     * 更新设备电量信息
     */
    async updateBatteryLevel(device) {
        try {
            const server = device.gatt;
            if (!server.connected) return;
            
            // 获取电池服务
            const batteryService = await server.getPrimaryService('battery_service');
            const batteryLevelChar = await batteryService.getCharacteristic('battery_level');
            const batteryValue = await batteryLevelChar.readValue();
            const batteryLevel = batteryValue.getUint8(0);
            
            // 更新电量信息
            const deviceInfo = this.devices.get(device.id);
            if (deviceInfo) {
                deviceInfo.batteryLevel = batteryLevel;
                
                // 触发电量更新事件
                this.dispatchEvent(new CustomEvent('batteryLevelUpdated', {
                    detail: { 
                        deviceId: device.id, 
                        batteryLevel 
                    }
                }));
            }
            
        } catch (error) {
            console.log('Battery service not available for this device');
        }
    }
    
    /**
     * 扫描新设备
     */
    async scanForDevices(filters = []) {
        if (this.isScanning) {
            return;
        }
        
        try {
            this.isScanning = true;
            
            // 触发扫描开始事件
            this.dispatchEvent(new CustomEvent('scanStarted'));
            
            // 使用原生API请求设备
            const device = await navigator.bluetooth.requestDevice({
                filters: filters.length > 0 ? filters : [{ namePrefix: "HA-" }],
                optionalServices: ['battery_service', '0000181c-0000-1000-8000-00805f9b34fb', '0000180a-0000-1000-8000-00805f9b34fb']
            });
            
            // 添加到设备列表
            this.devices.set(device.id, {
                device: device,
                isConnected: false,
                batteryLevel: null,
                lastSeen: new Date()
            });
            
            // 自动连接新设备
            await this.connectDevice(device.id);
            
            // 触发扫描成功事件
            this.dispatchEvent(new CustomEvent('scanCompleted', {
                detail: { newDevice: device }
            }));
            
            return device;
            
        } catch (error) {
            console.error('Scan failed:', error);
            
            // 触发扫描失败事件
            this.dispatchEvent(new CustomEvent('scanFailed', {
                detail: { error: error.message }
            }));
            
            throw error;
            
        } finally {
            this.isScanning = false;
        }
    }
    
    /**
     * 获取已连接的设备
     */
    getConnectedDevice() {
        if (!this.connectedDevice) return null;
        
        const deviceInfo = this.devices.get(this.connectedDevice.id);
        if (!deviceInfo) return null;
        
        return {
            id: this.connectedDevice.id,
            name: this.connectedDevice.name,
            batteryLevel: deviceInfo.batteryLevel,
            device: this.connectedDevice
        };
    }
    
    /**
     * 确保设备有断开连接监听器
     */
    ensureDisconnectListener(device) {
        // 检查设备是否已经有我们的监听器
        if (!device._bluetoothManagerListener) {
            const listener = () => {
                this.handleDeviceDisconnected(device);
            };
            
            device.addEventListener('gattserverdisconnected', listener);
            device._bluetoothManagerListener = listener;
            
            console.log('🔗 Added disconnect listener for device:', device.name);
        }
    }
    
    /**
     * 检查并更新已连接设备的状态（用于外部连接的设备）
     */
    registerExternalConnection(device) {
        console.log('📱 Registering external device connection:', device.name);
        
        // 查找或创建设备信息
        let deviceInfo = this.devices.get(device.id);
        if (!deviceInfo) {
            // 如果设备不在列表中，添加它
            this.devices.set(device.id, {
                device: device,
                isConnected: false,
                batteryLevel: null,
                lastSeen: new Date()
            });
            deviceInfo = this.devices.get(device.id);
        }
        
        // 更新连接状态
        deviceInfo.isConnected = true;
        this.connectedDevice = device;
        
        // 确保有断开监听器
        this.ensureDisconnectListener(device);
        
        // 尝试获取电量信息
        this.updateBatteryLevel(device);
        
        // 触发连接事件
        this.dispatchEvent(new CustomEvent('deviceConnected', {
            detail: { 
                deviceId: device.id, 
                deviceName: device.name,
                batteryLevel: deviceInfo.batteryLevel
            }
        }));
        
        // 更新设备列表
        this.dispatchEvent(new CustomEvent('devicesUpdated', {
            detail: { devices: this.getDevicesList() }
        }));
    }
    
    /**
     * 清理资源
     */
    destroy() {
        // 断开所有连接
        this.devices.forEach((info, id) => {
            if (info.isConnected) {
                this.disconnectDevice(id);
            }
        });
        
        this.devices.clear();
        this.connectedDevice = null;
    }
}

// 创建全局实例
export const bluetoothDeviceManager = new BluetoothDeviceManager(); 