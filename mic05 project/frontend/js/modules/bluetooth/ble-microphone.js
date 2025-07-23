// BLE麦克风模块
export class BLEMicrophone extends EventTarget {
    constructor() {
        super();
        this.device = null;
        this.gattServer = null;
        this.voiceService = null;
        this.voiceDataCharacteristic = null;
        this.functionModelCharacteristic = null;
        this.encodeTypeCharacteristic = null;
        this.isConnected = false;
        this.systemId = null;
        this.defaultEncodeType = "ADPCM_16K";
        
        // 服务和特征UUID
        this.voiceServiceUUID = '0000181c-0000-1000-8000-00805f9b34fb';
        this.voiceDataCharacteristicUUID = '00002bcd-0000-1000-8000-00805f9b34fb';
        this.functionModelCharacteristicUUID = '00002b7a-0000-1000-8000-00805f9b34fb';
        this.encodeTypeCharacteristicUUID = '00002b7b-0000-1000-8000-00805f9b34fb';
        
        // 状态管理
        this.lastDataReceivedTime = Date.now();
        this.isProcessingData = false;
        this.connectRetries = 0;
        this.maxRetries = 5;
    }
    
    // 搜索并连接设备
    async connect() {
        try {
            console.log('BLE: Searching for devices...');
            this.connectRetries = 0;
            
            const deviceOptions = {
                optionalServices: [this.voiceServiceUUID, '0000180a-0000-1000-8000-00805f9b34fb'],
                filters: [{ namePrefix: "HA-" }]
            };
            
            this.device = await navigator.bluetooth.requestDevice(deviceOptions);
            this.device.addEventListener('gattserverdisconnected', this.onDisconnected.bind(this));
            
            console.log('BLE: Connecting to:', this.device.name);
            await this.doConnect();
            
            return true;
        } catch (error) {
            console.error('BLE: Connection failed', error);
            this.dispatchEvent(new CustomEvent('error', { detail: error }));
            return false;
        }
    }
    
    // 连接到指定的设备
    async connectToDevice(device) {
        try {
            console.log('BLE: Connecting to device:', device.name);
            this.connectRetries = 0;
            
            this.device = device;
            this.device.addEventListener('gattserverdisconnected', this.onDisconnected.bind(this));
            
            await this.doConnect();
            
            return true;
        } catch (error) {
            console.error('BLE: Connection to device failed', error);
            this.dispatchEvent(new CustomEvent('error', { detail: error }));
            return false;
        }
    }
    
    // 执行连接
    async doConnect() {
        try {
            this.gattServer = await this.device.gatt.connect();
            console.log('BLE: Connected to GATT server');
            
            // 读取System ID
            try {
                const deviceInfoService = await this.gattServer.getPrimaryService('0000180a-0000-1000-8000-00805f9b34fb');
                const systemIdCharacteristic = await deviceInfoService.getCharacteristic('00002a23-0000-1000-8000-00805f9b34fb');
                const systemIdValue = await systemIdCharacteristic.readValue();
                this.systemId = Array.from(new Uint8Array(systemIdValue.buffer))
                    .map(b => b.toString(16).padStart(2, '0'))
                    .join('');
                console.log('BLE: System ID:', this.systemId);
            } catch (error) {
                console.warn('BLE: Could not read System ID', error);
            }
            
            await this.setupServices();
            this.isConnected = true;
            this.dispatchEvent(new CustomEvent('connected', { detail: { device: this.device, systemId: this.systemId } }));
            
        } catch (error) {
            console.error('BLE: Connection error', error);
            if (this.connectRetries < this.maxRetries) {
                this.connectRetries++;
                console.log(`BLE: Reconnecting... (${this.connectRetries}/${this.maxRetries})`);
                await new Promise(resolve => setTimeout(resolve, 2000));
                return this.doConnect();
            }
            throw error;
        }
    }
    
    // 设置BLE服务
    async setupServices() {
        console.log('🔧 BLE: Setting up services...');
        
        // 获取语音服务
        console.log('🔧 BLE: Getting voice service...', this.voiceServiceUUID);
        this.voiceService = await this.gattServer.getPrimaryService(this.voiceServiceUUID);
        console.log('✅ BLE: Found voice service');
        
        // 设置功能模式特征（按键控制）
        console.log('🔧 BLE: Setting up function model characteristic...', this.functionModelCharacteristicUUID);
        this.functionModelCharacteristic = await this.voiceService.getCharacteristic(this.functionModelCharacteristicUUID);
        await this.functionModelCharacteristic.startNotifications();
        this.functionModelCharacteristic.addEventListener('characteristicvaluechanged', this.handleFunctionModel.bind(this));
        console.log('✅ BLE: Subscribed to function model notifications');
        
        // 设置语音数据特征
        console.log('🔧 BLE: Setting up voice data characteristic...', this.voiceDataCharacteristicUUID);
        this.voiceDataCharacteristic = await this.voiceService.getCharacteristic(this.voiceDataCharacteristicUUID);
        await this.voiceDataCharacteristic.startNotifications();
        this.voiceDataCharacteristic.addEventListener('characteristicvaluechanged', this.handleVoiceData.bind(this));
        console.log('✅ BLE: Subscribed to voice data notifications');
        
        // 设置编码类型特征（如果支持）
        console.log('🔧 BLE: Setting up encode type characteristic (optional)...', this.encodeTypeCharacteristicUUID);
        try {
            this.encodeTypeCharacteristic = await this.voiceService.getCharacteristic(this.encodeTypeCharacteristicUUID);
            this.encodeTypeCharacteristic.addEventListener('characteristicvaluechanged', this.handleEncodeTypeChanged.bind(this));
            await this.encodeTypeCharacteristic.startNotifications();
            
            // 设置支持的编码类型
            await this.encodeTypeCharacteristic.writeValue(new TextEncoder().encode(JSON.stringify({
                "ADPCM_8K": { "is_supported": true, "is_default": false },
                "ADPCM_16K": { "is_supported": true, "is_default": true },
                "OPUS": { "is_supported": false, "is_default": false },
                "SPEEX": { "is_supported": true, "is_default": false }
            })));
            console.log('✅ BLE: Set supported encoding types');
        } catch (error) {
            console.warn('⚠️ BLE: Encode type characteristic not supported', error);
        }
        
        console.log('🎉 BLE: All services setup completed successfully!');
        console.log('🔧 BLE: Service status:');
        console.log('  - Voice service:', !!this.voiceService);
        console.log('  - Voice data characteristic:', !!this.voiceDataCharacteristic);
        console.log('  - Function model characteristic:', !!this.functionModelCharacteristic);
        console.log('  - Encode type characteristic:', !!this.encodeTypeCharacteristic);
    }
    
    // 处理功能模式（按键）事件
    handleFunctionModel(event) {
        const value = event.target.value.getUint8(0);
        console.log('BLE: Function model value:', value);
        
        this.dispatchEvent(new CustomEvent('buttonEvent', { detail: { value } }));
        
        // 录音结束
        if (value === 0) {
            this.dispatchEvent(new CustomEvent('recordingEnd'));
            console.log('BLE: Recording end button event triggered');
        }
        // 录音开始
        else if (value === 1) {
            this.dispatchEvent(new CustomEvent('recordingStart'));
            console.log('BLE: Recording start button event triggered');
        }
    }
    
    // 处理语音数据
    handleVoiceData(event) {
        const data = new Uint8Array(event.target.value.buffer);
        console.log('BLE: Received voice data, length:', data.length, 'First bytes:', Array.from(data.slice(0, 10)).map(b => '0x' + b.toString(16).padStart(2, '0')).join(' '));
        
        this.lastDataReceivedTime = Date.now();
        this.dispatchEvent(new CustomEvent('audioData', { detail: { data, encodeType: this.defaultEncodeType } }));
    }
    
    // 处理编码类型变化
    handleEncodeTypeChanged(event) {
        const data = new Uint8Array(event.target.value.buffer);
        const jsonString = new TextDecoder().decode(data);
        const encodeTypes = JSON.parse(jsonString);
        
        for (const [type, info] of Object.entries(encodeTypes)) {
            if (info.is_default) {
                this.defaultEncodeType = type;
                console.log('BLE: Default encode type:', type);
                break;
            }
        }
    }
    
    // 断开连接处理
    onDisconnected() {
        console.log('BLE: Device disconnected');
        this.isConnected = false;
        this.dispatchEvent(new CustomEvent('disconnected'));
        
        // 自动重连
        if (this.connectRetries < this.maxRetries) {
            console.log('BLE: Attempting to reconnect...');
            this.doConnect();
        }
    }
    
    // 主动断开连接
    disconnect() {
        if (this.device && this.device.gatt.connected) {
            this.device.gatt.disconnect();
        }
        this.reset();
    }
    
    // 重置状态
    reset() {
        this.device = null;
        this.gattServer = null;
        this.voiceService = null;
        this.voiceDataCharacteristic = null;
        this.functionModelCharacteristic = null;
        this.encodeTypeCharacteristic = null;
        this.isConnected = false;
        this.connectRetries = 0;
    }
    
    // 发送控制指令
    async sendCommand(command) {
        if (!this.functionModelCharacteristic) {
            throw new Error('Not connected to device');
        }
        
        const commandValue = typeof command === 'string' ? command.charCodeAt(0) : command;
        await this.functionModelCharacteristic.writeValue(new Uint8Array([commandValue]));
        console.log('BLE: Sent command:', command);
    }
}