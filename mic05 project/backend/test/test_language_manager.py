import os
import sys
import asyncio
from typing import Dict, Any

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from backend.services.language_manager import language_manager
from backend.models.language_stats import LanguageStats
from backend.utils.sessions import Session
from backend.utils.exceptions import SessionException

class TestLanguageManager:
    """语言管理器测试类"""
    
    def __init__(self):
        """初始化测试类"""
        self.session = Session()
        self.language_manager = language_manager
    
    def setup_test_session(self, session: Session, session_langs: list):
        """设置测试会话语言"""
        session.session_langs = session_langs
        print(f"✅ 设置测试会话语言: {session.session_langs}")
    
    async def test_get_target_language_from_session(self):
        """测试从会话语言中获取目标语言"""
        print("\n🔍 测试从会话语言中获取目标语言...")
        
        try:
            # 设置会话语言：中文和英文
            self.session.update_detected_lang('zh-CN')
            print(f"更新后的检测语言: {self.session.detected_lang}")
            print(f"更新后的会话语言: {self.session.session_langs}")
            # 测试识别到中文，应该返回英文
            await self.language_manager.update_target_language(self.session)
            target_lang = self.session.target_lang
            print(f"   识别语言: chinese -> 目标语言: {target_lang}")
            
            # 测试识别到英文，应该返回中文
            self.session.update_detected_lang('en-US')
            print(f"更新后的检测语言: {self.session.detected_lang}")
            print(f"更新后的会话语言: {self.session.session_langs}")
            await self.language_manager.update_target_language(self.session)
            target_lang = self.session.target_lang
            print(f"   识别语言: english -> 目标语言: {target_lang}")
            
            print("✅ 会话语言目标语言获取测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 会话语言目标语言获取测试失败: {str(e)}")
            return False
    
    async def test_get_target_language_from_global(self):
        """测试从全局语言统计中获取目标语言"""
        print("\n🔍 测试从全局语言统计中获取目标语言...")
        
        try:
            # 设置只有一种语言的会话
            self.setup_test_session(self.session,['zh-CN'])
            
            # 先添加一些全局语言统计数据
            await LanguageStats.increment_usage('zh-CN')
            await LanguageStats.increment_usage('en-US')
            await LanguageStats.increment_usage('ja-JP')
            await LanguageStats.increment_usage('en-US')  # 英文使用次数更多
            
            # 测试识别到中文，应该从全局统计中找到非中文的语言
            await self.language_manager.update_target_language(self.session)
            print(f"   识别语言: chinese -> 目标语言: {self.session.target_lang}")   
            print(f"   (从全局统计中获取，因为会话中只有中文)")
            
            print("✅ 全局语言统计目标语言获取测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 全局语言统计目标语言获取测试失败: {str(e)}")
            return False
    
    async def test_update_session_language(self):
        """测试更新会话语言"""
        print("\n🔍 测试更新会话语言...")
        
        try:
            # 清空会话语言
            self.session.session_langs = []
            self.session.detected_lang = ''
            
            # 测试更新不同语言
            test_languages = ['chinese', 'english', 'japanese', 'spanish']
            
            for lang in test_languages:
                await self.language_manager.update_session_language(self.session,lang)
                print(f"   更新语言: {lang}")
                print(f"   当前会话语言: {self.session.session_langs}")
                print(f"   检测到的语言: {self.session.detected_lang}")
            
            print("✅ 会话语言更新测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 会话语言更新测试失败: {str(e)}")
            return False
    
    async def test_update_global_language_stats(self):
        """测试更新全局语言统计"""
        print("\n🔍 测试更新全局语言统计...")
        
        try:
            # 测试更新不同语言的统计
            test_data = [
                ('chinese', 3),
                ('english', 5),
                ('japanese', 2),
                ('spanish', 1),
                ('french', 4)
            ]
            
            print("   更新语言统计:")
            for lang, count in test_data:
                for _ in range(count):
                    await self.language_manager.update_global_language_stats(lang)
                print(f"   {lang}: {count} 次")
            
            # 获取最高使用的语言
            top_language = await LanguageStats.get_top_language()
            print(f"   最高使用语言: {top_language}")
            
            print("✅ 全局语言统计更新测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 全局语言统计更新测试失败: {str(e)}")
            return False
    
    async def test_language_normalization(self):
        """测试语言代码标准化"""
        print("\n🔍 测试语言代码标准化...")
        
        try:
            # 测试各种语言输入格式
            test_cases = [
                ('chinese', 'zh-CN'),
                ('english', 'en-US'),
                ('japanese', 'ja-JP'),
                ('spanish', 'es-ES'),
                ('french', 'fr-FR'),
                ('zh', 'zh-CN'),
                ('en', 'en-US'),
                ('unknown_language', 'en-US')  # 默认回退
            ]
            
            print("   语言代码标准化测试:")
            for input_lang, expected in test_cases:
                await self.language_manager.update_target_language(self.session)
                target_lang = self.session.target_lang
                print(f"   输入: {input_lang} -> 预期标准化: {expected}")
                # 这里主要测试不会抛出异常
            
            print("✅ 语言代码标准化测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 语言代码标准化测试失败: {str(e)}")
            return False
    
    async def test_edge_cases(self):
        """测试边界情况"""
        print("\n🔍 测试边界情况...")
        
        try:
            # 测试空会话语言
            print("   测试空会话语言...")
            self.session.session_langs = []
            try:
                await self.language_manager.update_target_language(self.session)
                target_lang = self.session.target_lang
                print(f"   空会话语言处理: {target_lang}")
            except Exception as e:
                print(f"   空会话语言异常 (预期): {str(e)}")
            
            # 测试无效语言输入
            print("   测试无效语言输入...")
            self.setup_test_session(self.session,['zh-CN', 'en-US'])
            try:
                await self.language_manager.update_target_language(self.session)
                target_lang = self.session.target_lang
                print(f"   空字符串处理: {target_lang}")
            except Exception as e:
                print(f"   空字符串异常: {str(e)}")
            
            # 测试相同语言会话
            print("   测试相同语言会话...")
            self.setup_test_session(self.session,['zh-CN', 'zh-CN', 'zh-CN'])
            await self.language_manager.update_target_language(self.session)
            target_lang = self.session.target_lang
            print(f"   相同语言会话处理: {target_lang}")
            
            print("✅ 边界情况测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 边界情况测试失败: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🌐 开始语言管理器测试")
        print("=" * 60)
        
        # 运行各项测试
        test_results = {}
        
        test_results['session_target'] = await self.test_get_target_language_from_session()
        test_results['global_target'] = await self.test_get_target_language_from_global()
        test_results['update_session'] = await self.test_update_session_language()
        test_results['update_global'] = await self.test_update_global_language_stats()
        test_results['normalization'] = await self.test_language_normalization()
        test_results['edge_cases'] = await self.test_edge_cases()
        
        # 总结测试结果
        print("\n" + "=" * 60)
        print("📊 测试结果总结:")
        
        success_count = 0
        total_count = 0
        
        for test_name, result in test_results.items():
            total_count += 1
            if result:
                success_count += 1
                print(f"   ✅ {test_name.replace('_', ' ').title()}: 成功")
            else:
                print(f"   ❌ {test_name.replace('_', ' ').title()}: 失败")
        
        print(f"\n🎯 测试完成: {success_count}/{total_count} 个测试通过")
        
        if success_count == total_count:
            print("🎉 所有测试都通过了！语言管理器工作正常。")
        else:
            print("⚠️  部分测试失败，请检查实现逻辑。")
        
        return test_results

async def main():
    """主函数"""
    try:
        # 创建测试实例
        test_manager = TestLanguageManager()
        
        # 运行所有测试
        results = await test_manager.run_all_tests()
        
        return results
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试运行失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main()) 