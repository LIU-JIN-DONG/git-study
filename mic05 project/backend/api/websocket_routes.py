import json
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from typing import Optional
import logging
import asyncio
from starlette.responses import HTMLResponse

from services.websocket_service import websocket_manager

logging.basicConfig(level=logging.INFO)
ws_router = APIRouter()

@ws_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: Optional[str] = Query(None,description="会话ID,如果为空则创建新会话,8位随机数")
):
    """
    WebSocket 端点,用于处理WebSocket连接和消息

    Args:
        websocket: WebSocket 连接实例
        session_id: 会话ID,如果为空则创建新会话,8位随机数
    """
    current_session_id = None

    try:
        # 建立连接
        current_session_id = await websocket_manager.connect(websocket,session_id)
        if not current_session_id:
            await websocket.close(code=1008,reason="Session creation failed")
            return

        # 消息循环
        while True:
            try: 
                # 接受消息
                data = await websocket.receive_json()
                
                # 处理消息
                await websocket_manager.handle_message(current_session_id,data)

            except WebSocketDisconnect:
                logging.info(f"WebSocket disconnected: {current_session_id}")
                break
            except Exception as e:
                await websocket_manager._send_error_message(
                    current_session_id,
                    f"Internal server error: {str(e)}"
                )
                logging.error(f"WebSocket error: {str(e)}")
                break
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected: {current_session_id}")
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
    finally:
        # 清理连接
        if current_session_id:
            await websocket_manager.disconnect(current_session_id)

@ws_router.get("/ws/test")
async def websocket_test_page():
    """
    WebSocket测试页面
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket测试</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #messages { 
                border: 1px solid #ccc; 
                height: 400px; 
                overflow-y: scroll; 
                padding: 10px; 
                background-color: #f9f9f9;
                margin-bottom: 20px;
            }
            button { 
                margin: 5px; 
                padding: 10px 15px; 
                background-color: #007bff; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                cursor: pointer;
            }
            button:hover { background-color: #0056b3; }
            .connected { background-color: #28a745; }
            .disconnected { background-color: #dc3545; }
        </style>
    </head>
    <body>
        <h1>MIC05 WebSocket测试</h1>
        <div id="status">状态: 未连接</div>
        <div id="messages"></div>
        
        <div>
            <button id="connectBtn" onclick="connect()">连接</button>
            <button id="disconnectBtn" onclick="disconnect()">断开</button>
            <button onclick="sendPing()">发送心跳</button>
            <button onclick="getSystemStatus()">获取系统状态</button>
            <button onclick="sendTestAudio()">模拟音频流</button>
            <button onclick="changeLanguage()">切换语言(日语)</button>
        </div>
        
        <script>
            let ws = null;
            let sessionId = null;
            
            function updateStatus(status, isConnected) {
                const statusDiv = document.getElementById('status');
                statusDiv.textContent = '状态: ' + status;
                statusDiv.className = isConnected ? 'connected' : 'disconnected';
            }
            
            function log(message) {
                const messages = document.getElementById('messages');
                const time = new Date().toLocaleTimeString();
                messages.innerHTML += '<p><strong>' + time + ':</strong> ' + message + '</p>';
                messages.scrollTop = messages.scrollHeight;
            }
            
            function connect() {
                if (ws) {
                    ws.close();
                }
                
                updateStatus('连接中...', false);
                ws = new WebSocket('ws://localhost:8000/ws');
                
                ws.onopen = function(event) {
                    updateStatus('已连接', true);
                    log('✅ WebSocket连接已建立');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    log('📨 收到消息: ' + JSON.stringify(data, null, 2));
                    
                    if (data.type === 'connected') {
                        sessionId = data.data.session_id;
                        log('🆔 会话ID: ' + sessionId);
                        log('🌍 支持语言: ' + data.data.supported_languages.join(', '));
                    }
                };
                
                ws.onclose = function(event) {
                    updateStatus('已断开', false);
                    log('❌ WebSocket连接已关闭');
                };
                
                ws.onerror = function(error) {
                    updateStatus('连接错误', false);
                    log('🚨 WebSocket错误: ' + error);
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }
            
            function sendMessage(message) {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify(message));
                    log('📤 发送消息: ' + JSON.stringify(message, null, 2));
                } else {
                    log('❌ WebSocket未连接');
                }
            }
            
            function sendPing() {
                sendMessage({
                    type: 'ping',
                    data: {
                        timestamp: new Date().toISOString()
                    }
                });
            }
            
            function getSystemStatus() {
                sendMessage({
                    type: 'get_system_status',
                    data: {}
                });
            }
            
            function sendTestAudio() {
                // 模拟音频流消息
                sendMessage({
                    type: 'audio_stream',
                    data: {
                        audio_chunk: btoa('fake_audio_data_您好今天是星期二天气晴朗'),
                        chunk_id: 'chunk_001',
                        is_final: true,
                        sample_rate: 16000,
                        format: 'wav'
                    }
                });
            }
            
            function changeLanguage() {
                sendMessage({
                    type: 'change_target_language',
                    data: {
                        current_language: 'ja-JP'
                    }
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@ws_router.get("/ws/sessions")
async def get_active_sessions():
    """
    获取当前活跃的会话列表
    
    Returns:
        dict: 包含活跃会话信息的字典
    """
    try:
        active_sessions = websocket_manager.get_active_sessions()
        session_details = []
        
        for session_id in active_sessions:
            session_status = websocket_manager.get_session_status(session_id)
            if session_status:
                session_details.append(session_status)
        
        return {
            "success": True,
            "data": {
                "active_session_count": len(active_sessions),
                "sessions": session_details
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@ws_router.get("/ws/system-status")
async def get_system_status():
    """
    获取系统状态
    
    Returns:
        dict: 系统状态信息
    """
    try:
        return {
            "success": True,
            "data": websocket_manager.system_status
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@ws_router.get("/ws/admin")
async def websocket_admin_page():
    """
    WebSocket管理界面
    """
    try:
        with open('backend-admin.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <head><title>管理界面未找到</title></head>
        <body>
        <h1>管理界面未找到</h1>
        <p>请确保 backend-admin.html 文件存在于项目根目录</p>
        </body>
        </html>
        """, status_code=404)