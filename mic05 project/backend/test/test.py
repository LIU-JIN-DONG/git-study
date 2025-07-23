import asyncio
import uuid
from datetime import datetime

# 仅导入 Session 类
from utils.sessions import Session

async def test_session():
    """测试会话类的基本功能，不涉及数据库操作"""
    print("\n===== 测试 Session 类 =====")
    
    # 创建会话
    session_id = f"test_{str(uuid.uuid4())[:8]}"
    session = Session(session_id)
    print(f"创建会话: {session.session_id}")
    
    # 更新检测到的语言
    session.update_detected_language("zh-CN")
    print(f"更新检测到的语言: {session.detected_lang}")
    
    # 手动设置目标语言，跳过数据库查询
    # 替代 await session.set_target_language() 调用
    session.target_lang = "en-US"
    if "en-US" not in session.session_langs:
        session.session_langs.append("en-US")
    print(f"手动设置目标语言: {session.target_lang}")
    print(f"会话语言数组: {session.session_langs}")

    # 添加对话记录
    session.add_to_conversation("你好", "Hello", "zh-CN", "en-US", datetime.now().isoformat())
    session.add_to_conversation("我是Claude", "I am Claude", "zh-CN", "en-US", datetime.now().isoformat())
    print(f"对话记录数量: {len(session.conversation)}")
    print(f"对话记录示例: {session.conversation[0]}")
    
    # 测试获取非目标语言
    non_target_langs = [lang for lang in session.session_langs if lang != session.target_lang]
    print(f"非目标语言: {non_target_langs}")
    
    # 模拟更新目标语言
    old_target = session.target_lang
    session.target_lang = "ja-JP"
    if "ja-JP" not in session.session_langs:
        session.session_langs.append("ja-JP")
    print(f"更新目标语言: 从 {old_target} 到 {session.target_lang}")
    print(f"更新后的会话语言数组: {session.session_langs}")
    
    # 添加更多对话记录
    session.add_to_conversation("你好吗", "お元気ですか", "zh-CN", "ja-JP", datetime.now().isoformat())
    print(f"更新后的对话记录数量: {len(session.conversation)}")
    
    return session

def main():
    """主测试函数"""
    try:
        # 运行会话测试
        session = asyncio.run(test_session())
        
        # 打印会话信息
        print("\n===== 会话信息 =====")
        print(f"会话ID: {session.session_id}")
        print(f"目标语言: {session.target_lang}")
        print(f"检测到的语言: {session.detected_lang}")
        print(f"会话语言数组: {session.session_langs}")
        print(f"对话记录数量: {len(session.conversation)}")
        print(f"创建时间: {session.created_at}")
        print(f"更新时间: {session.updated_at}")
        
        print("\n===== 所有测试完成 =====")
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行测试
    main()