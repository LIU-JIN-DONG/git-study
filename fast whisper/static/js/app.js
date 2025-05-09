// 全局变量
let mediaRecorder;
let audioChunks = [];
let recordingStartTime;
let recordingTimer;
let recordingActive = false;
let websocket = null;
let webSocketConnected = false;

// 服务端VAD配置
const serverVADConfig = {
    vad_filter: true,                // 是否启用VAD过滤
    vad_threshold: 0.5,              // VAD阈值(0-1之间，越高越严格)
    min_speech_duration_ms: 250,     // 最小语音持续时间(毫秒)
    min_silence_duration_ms: 2000,   // 最小静默持续时间(毫秒)
    speech_pad_ms: 300               // 语音片段前后填充时间(毫秒)
};

// DOM元素
const startRecordingBtn = document.getElementById('startRecording');
const stopRecordingBtn = document.getElementById('stopRecording');
const audioFileInput = document.getElementById('audioFile');
const recordingStatus = document.getElementById('recordingStatus');
const timeElapsed = document.getElementById('timeElapsed');
const liveTranscription = document.getElementById('liveTranscription');
const completeTranscription = document.getElementById('completeTranscription');
const processingIndicator = document.getElementById('processingIndicator');
const transcriptionHistory = document.getElementById('transcriptionHistory');

// 初始化
function init() {
    console.log('应用初始化...');
    // 为按钮添加事件监听器
    startRecordingBtn.addEventListener('click', startRecording);
    stopRecordingBtn.addEventListener('click', stopRecording);
    audioFileInput.addEventListener('change', handleFileUpload);

    // 设置面板事件监听
    initSettingsPanel();

    // 检查麦克风权限
    checkMicrophonePermission();

    // 初始化WebSocket连接
    initWebSocket();
}

// 初始化设置面板
function initSettingsPanel() {
    const showSettingsBtn = document.getElementById('showSettingsBtn');
    const closeSettingsBtn = document.getElementById('closeSettingsBtn');
    const settingsPanel = document.getElementById('settingsPanel');
    const applySettingsBtn = document.getElementById('applySettingsBtn');

    // 阈值滑块实时显示
    const vadThreshold = document.getElementById('vadThreshold');
    const vadThresholdValue = document.getElementById('vadThresholdValue');

    // 显示设置面板
    showSettingsBtn.addEventListener('click', () => {
        settingsPanel.classList.remove('hidden');
    });

    // 关闭设置面板
    closeSettingsBtn.addEventListener('click', () => {
        settingsPanel.classList.add('hidden');
    });

    // 更新阈值显示
    vadThreshold.addEventListener('input', () => {
        vadThresholdValue.textContent = vadThreshold.value;
    });

    // 应用设置
    applySettingsBtn.addEventListener('click', () => {
        // 收集设置值
        const newConfig = {
            vad_filter: document.getElementById('vadFilter').checked,
            vad_threshold: parseFloat(document.getElementById('vadThreshold').value),
            min_speech_duration_ms: parseInt(document.getElementById('minSpeechDuration').value),
            min_silence_duration_ms: parseInt(document.getElementById('minSilenceDuration').value),
            speech_pad_ms: parseInt(document.getElementById('speechPadMs').value)
        };

        // 更新并发送设置
        updateServerVADConfig(newConfig);

        // 关闭设置面板
        settingsPanel.classList.add('hidden');

        // 显示提示
        recordingStatus.querySelector('.text').textContent = 'VAD设置已更新';
        setTimeout(() => {
            if (!recordingActive) {
                recordingStatus.querySelector('.text').textContent = '准备就绪';
            }
        }, 2000);
    });
}

// 初始化WebSocket连接
function initWebSocket() {
    // 确定WebSocket URL (基于当前页面URL)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    console.log(`正在连接WebSocket: ${wsUrl}`);

    try {
        websocket = new WebSocket(wsUrl);

        // 监听WebSocket事件
        websocket.onopen = (event) => {
            console.log('WebSocket连接已建立');
            webSocketConnected = true;
            // 更新UI以反映连接状态
            recordingStatus.querySelector('.text').textContent = '准备就绪';

            // 发送服务端VAD配置
            sendServerVADConfig();
        };

        websocket.onmessage = (event) => {
            console.log(`收到WebSocket消息: ${event.data}`);
            handleWebSocketMessage(event.data);
        };

        websocket.onerror = (error) => {
            console.error('WebSocket错误:', error);
            webSocketConnected = false;
            // 更新UI以反映连接状态
            recordingStatus.querySelector('.text').textContent = 'WebSocket连接错误';
        };

        websocket.onclose = (event) => {
            console.log('WebSocket连接已关闭');
            webSocketConnected = false;
            // 尝试重新连接
            setTimeout(initWebSocket, 3000);
        };
    } catch (error) {
        console.error('初始化WebSocket失败:', error);
    }
}

// 发送服务端VAD配置
function sendServerVADConfig() {
    if (webSocketConnected) {
        try {
            const configMsg = `CONFIG:VAD:${JSON.stringify(serverVADConfig)}`;
            websocket.send(configMsg);
            console.log('已发送服务端VAD配置:', serverVADConfig);
        } catch (error) {
            console.error('发送VAD配置失败:', error);
        }
    }
}

// 更新服务端VAD配置参数
function updateServerVADConfig(newConfig) {
    // 更新配置
    Object.assign(serverVADConfig, newConfig);

    // 发送到服务器
    sendServerVADConfig();

    console.log('已更新服务端VAD配置:', serverVADConfig);
}

// 处理从WebSocket接收到的消息
function handleWebSocketMessage(message) {
    // 处理不同类型的消息
    if (message.startsWith('PARTIAL_RESULT:')) {
        // 显示部分转录结果
        const result = message.substring('PARTIAL_RESULT:'.length);
        liveTranscription.textContent = result;
    }
    else if (message.startsWith('FINAL_RESULT:')) {
        // 显示最终转录结果
        const result = message.substring('FINAL_RESULT:'.length);
        completeTranscription.textContent = result;

        // 隐藏处理指示器
        processingIndicator.classList.remove('active');

        // 更新状态
        recordingStatus.querySelector('.text').textContent = '转录完成';

        // 添加到历史记录
        addToHistory({ text: result });
    }
    else if (message.startsWith('ERROR:')) {
        // 显示错误消息
        const error = message.substring('ERROR:'.length);
        console.error(`服务器错误: ${error}`);

        // 隐藏处理指示器
        processingIndicator.classList.remove('active');

        // 更新状态
        recordingStatus.querySelector('.text').textContent = '处理失败';

        // 显示错误消息
        alert(`音频处理失败: ${error}`);
    }
}

// 检查麦克风权限
async function checkMicrophonePermission() {
    try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('麦克风权限获取成功');
    } catch (error) {
        console.error('无法访问麦克风:', error);
        startRecordingBtn.disabled = true;
        startRecordingBtn.title = '麦克风访问被拒绝';
    }
}

// 开始录音
async function startRecording() {
    try {
        // 检查WebSocket连接
        if (!webSocketConnected) {
            alert('WebSocket连接未建立，无法进行实时转录。正在尝试重新连接...');
            initWebSocket();
            return;
        }

        console.log('开始录音...');
        // 清空之前的录音
        audioChunks = [];

        // 获取麦克风
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // 支持的MIME类型检查
        const mimeType = getSupportedMimeType();
        console.log('使用MIME类型:', mimeType);

        // 创建MediaRecorder实例
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: mimeType,
            audioBitsPerSecond: 128000
        });

        // 设置数据可用时的处理逻辑
        mediaRecorder.ondataavailable = async (event) => {
            if (event.data.size > 0) {
                console.log(`接收到音频数据块: ${event.data.size} 字节`);
                audioChunks.push(event.data);

                // 实时发送音频数据到WebSocket
                try {
                    // 将Blob转换为ArrayBuffer
                    const arrayBuffer = await event.data.arrayBuffer();
                    const base64Data = bufferToBase64(arrayBuffer);

                    // 发送数据到WebSocket
                    if (webSocketConnected) {
                        websocket.send(`DATA:${base64Data}`);
                    }
                } catch (error) {
                    console.error('处理/发送音频数据出错:', error);
                }
            }
        };

        // 设置录音停止时的处理逻辑
        mediaRecorder.onstop = async () => {
            console.log(`录音结束，共 ${audioChunks.length} 个音频块`);

            // 通知WebSocket录音停止
            if (webSocketConnected) {
                websocket.send("STOP_RECORDING");
            }
        };

        // 通知WebSocket开始录音
        if (webSocketConnected) {
            websocket.send("START_RECORDING");
        }

        // 开始录音
        mediaRecorder.start(500); // 每0.5秒保存一次数据，提高实时性

        // 更新UI
        recordingActive = true;
        startRecordingBtn.disabled = true;
        stopRecordingBtn.disabled = false;
        recordingStatus.classList.add('recording');
        recordingStatus.querySelector('.text').textContent = '正在录音...';

        // 开始计时
        recordingStartTime = Date.now();
        updateTimer();
        recordingTimer = setInterval(updateTimer, 1000);

        // 清空转录区域
        liveTranscription.textContent = '';
        completeTranscription.textContent = '';
    } catch (error) {
        console.error('录音失败:', error);
        alert('无法启动录音。请确保您已允许浏览器访问麦克风。');
    }
}

// 将ArrayBuffer转换为Base64字符串
function bufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

// 获取浏览器支持的MIME类型
function getSupportedMimeType() {
    const possibleTypes = [
        'audio/webm',
        'audio/webm;codecs=opus',
        'audio/ogg;codecs=opus',
        'audio/mp4',
        'audio/mpeg'
    ];

    for (let type of possibleTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
            return type;
        }
    }

    console.warn('没有找到支持的MIME类型，使用默认类型');
    return '';  // 使用默认类型
}

// 停止录音
function stopRecording() {
    if (mediaRecorder && recordingActive) {
        console.log('停止录音...');
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());

        // 更新UI
        recordingActive = false;
        startRecordingBtn.disabled = false;
        stopRecordingBtn.disabled = true;
        recordingStatus.classList.remove('recording');
        recordingStatus.querySelector('.text').textContent = '正在处理...';

        // 停止计时
        clearInterval(recordingTimer);

        // 显示处理指示器
        processingIndicator.classList.add('active');
    }
}

// 更新计时器
function updateTimer() {
    const elapsedMilliseconds = Date.now() - recordingStartTime;
    const elapsedSeconds = Math.floor(elapsedMilliseconds / 1000);
    const minutes = Math.floor(elapsedSeconds / 60);
    const seconds = elapsedSeconds % 60;

    timeElapsed.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

// 处理音频文件上传
async function handleFileUpload(event) {
    const file = event.target.files[0];

    if (!file) return;

    console.log(`用户上传文件: ${file.name}, 大小: ${file.size} 字节, 类型: ${file.type}`);

    const allowedTypes = [
        'audio/mp3', 'audio/mpeg', 'audio/wav',
        'audio/x-m4a', 'audio/m4a', 'audio/ogg', 'audio/flac'
    ];

    // 检查文件扩展名
    const fileExtension = file.name.split('.').pop().toLowerCase();
    const validExtensions = ['mp3', 'wav', 'm4a', 'ogg', 'flac'];

    // 检查文件类型
    if (!allowedTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
        console.error(`不支持的文件类型: ${file.type}, 扩展名: ${fileExtension}`);
        alert('请上传支持的音频格式: MP3, WAV, M4A, OGG, FLAC');
        return;
    }

    // 更新UI
    recordingStatus.querySelector('.text').textContent = '正在处理上传的文件...';

    // 清空转录区域
    liveTranscription.textContent = '';
    completeTranscription.textContent = '';

    // 显示处理指示器
    processingIndicator.classList.add('active');

    // 处理音频
    await processAudio(file);
}

// 处理音频并发送到API
async function processAudio(audioData) {
    try {
        console.log('开始处理音频...');
        // 创建FormData对象
        const formData = new FormData();
        formData.append('audio_file', audioData);

        console.log(`准备发送到服务器的数据: 文件名=${audioData.name}, 大小=${audioData.size}字节, 类型=${audioData.type}`);

        // 发送请求到服务器
        console.log('发送请求到服务器...');
        const response = await fetch('/transcribe', {
            method: 'POST',
            body: formData
        });

        console.log(`服务器响应状态: ${response.status}`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`服务器错误: ${response.status} - ${errorText}`);
            throw new Error(`HTTP错误! 状态: ${response.status}, 详情: ${errorText}`);
        }

        // 解析响应
        const result = await response.json();
        console.log('收到转录结果:', result);

        // 隐藏处理指示器
        processingIndicator.classList.remove('active');

        // 更新UI
        recordingStatus.querySelector('.text').textContent = '转录完成';

        // 显示转录结果
        displayTranscription(result);

        // 将结果添加到历史记录
        addToHistory(result);
    } catch (error) {
        console.error('处理音频失败:', error);

        // 隐藏处理指示器
        processingIndicator.classList.remove('active');

        // 更新UI
        recordingStatus.querySelector('.text').textContent = '处理失败';
        alert(`音频处理失败: ${error.message}`);
    }
}

// 显示转录结果
function displayTranscription(result) {
    // 显示完整的转录文本
    completeTranscription.textContent = result.text;

    // 清除之前的实时转录
    liveTranscription.textContent = '';

    // 如果有分段信息，以此创建更丰富的显示
    if (result.segments && result.segments.length > 0) {
        console.log(`收到 ${result.segments.length} 个文本段落`);
        // 可以在这里添加更多的显示逻辑，如分段显示、时间戳等
    }
}

// 添加到历史记录
function addToHistory(result) {
    // 创建历史记录项
    const historyItem = document.createElement('div');
    historyItem.className = 'history-item';

    // 添加时间
    const timeElement = document.createElement('div');
    timeElement.className = 'time';
    timeElement.textContent = new Date().toLocaleTimeString();
    historyItem.appendChild(timeElement);

    // 添加文本
    const textElement = document.createElement('div');
    textElement.className = 'text';
    textElement.textContent = result.text;
    historyItem.appendChild(textElement);

    // 将项目添加到历史记录
    transcriptionHistory.prepend(historyItem);
}

// 初始化应用
document.addEventListener('DOMContentLoaded', init); 