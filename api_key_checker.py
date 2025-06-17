#!/usr/bin/env python3
"""
API Key 有效性检测脚本 - 使用OpenAI SDK完全模拟NovAnything服务内部的请求方式
使用方法: python api_key_checker.py
"""

import json
import time
import traceback

try:
    from openai import OpenAI
    print("✅ OpenAI SDK 已导入")
except ImportError:
    print("❌ 请先安装 OpenAI SDK: pip install openai")
    exit(1)

def test_service_api_key_with_sdk(api_key, api_base, model):
    """
    使用OpenAI SDK完全模拟NovAnything服务内部的API调用方式
    """
    print(f"🔍 测试 API Key: {api_key[:20]}...")
    print(f"🌐 API Base: {api_base}")
    print(f"🤖 模型: {model}")
    
    try:
        # 完全模拟服务内部的OpenAI客户端创建方式
        client = OpenAI(base_url=api_base, api_key=api_key)
        print(f"📡 OpenAI客户端创建成功")
        
        # 模拟服务内部的消息格式
        messages = [
            {"role": "user", "content": "测试连接"}
        ]
        
        print(f"📤 发送请求...")
        
        # 完全模拟服务内部的调用方式
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            max_tokens=10,
            temperature=0.5,
            top_p=0.99,
            stop=None
        )
        
        print(f"✅ API Key 有效!")
        print(f"📝 测试响应: {response.choices[0].message.content}")
        
        # 显示详细信息
        if hasattr(response, 'usage') and response.usage:
            print(f"📈 Token使用: {response.usage}")
        
        if hasattr(response, 'model'):
            print(f"🎯 实际使用模型: {response.model}")
            
        return True
        
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        
        print(f"❌ 调用失败: {error_type}")
        print(f"📄 错误详情: {error_message}")
        
        # 详细的错误分析
        if "401" in error_message or "Unauthorized" in error_message or "invalid" in error_message.lower():
            print(f"🔑 这是认证错误 - API Key无效或已过期")
        elif "429" in error_message or "rate" in error_message.lower():
            print(f"⚠️ 这是限流错误 - API调用过于频繁或配额用尽")
        elif "403" in error_message or "permission" in error_message.lower():
            print(f"🚫 这是权限错误 - API Key权限不足")
        elif "timeout" in error_message.lower() or "connection" in error_message.lower():
            print(f"🌐 这是网络错误 - 连接超时或网络问题")
        else:
            print(f"🔥 其他错误类型")
            
        # 打印完整的错误堆栈（用于调试）
        print(f"🐛 完整错误堆栈:")
        print(traceback.format_exc())
        
        return False

def main():
    print("=" * 80)
    print("🚀 NovAnything API Key 有效性检测工具")
    print("🎯 使用OpenAI SDK完全模拟服务内部的请求方式")
    print("=" * 80)
    
    # 根据你的配置截图设置的测试项目
    test_configs = [
        {
            "name": "当前实际使用的配置 (火山引擎豆包)",
            "api_key": "99ea7d5b-ce3e-4406-88f1-9d3a0981de94",
            "api_base": "https://ark.cn-beijing.volces.com/api/v3", 
            "model": "deepseek-v3-250324"
        },
        {
            "name": "之前配置的Key (第一个sk开头)",
            "api_key": "sk-d9d8a4d62fbd4423be4e941df712dc06",
            "api_base": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "deepseek-v3-250324"
        },
        {
            "name": "之前配置的Key (第二个sk开头)",
            "api_key": "sk-d2fdb0fd84874dabb55821d3869f6d43",
            "api_base": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo"
        }
    ]
    
    print(f"📋 将测试 {len(test_configs)} 个配置")
    print()
    
    valid_configs = []
    invalid_configs = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"[{i}/{len(test_configs)}] 测试配置: {config['name']}")
        print("=" * 60)
        
        if test_service_api_key_with_sdk(config['api_key'], config['api_base'], config['model']):
            valid_configs.append(config)
        else:
            invalid_configs.append(config)
            
        print("-" * 80)
        
        # 避免请求过于频繁
        if i < len(test_configs):
            print(f"⏳ 等待 3 秒避免请求过于频繁...")
            time.sleep(3)
    
    # 总结报告
    print()
    print("📊 测试结果总结:")
    print(f"✅ 有效的配置: {len(valid_configs)} 个")
    print(f"❌ 无效的配置: {len(invalid_configs)} 个")
    
    if valid_configs:
        print("\n🎉 可以使用的配置:")
        for config in valid_configs:
            print(f"   ✓ {config['name']}")
            print(f"     API Key: {config['api_key'][:20]}...")
            print(f"     模型: {config['model']}")
            print(f"     API Base: {config['api_base']}")
    
    if invalid_configs:
        print("\n⚠️ 需要检查的配置:")
        for config in invalid_configs:
            print(f"   ✗ {config['name']}")
            print(f"     API Key: {config['api_key'][:20]}...")
            print(f"     模型: {config['model']}")
            print(f"     API Base: {config['api_base']}")
    
    print()
    print("💡 建议:")
    if valid_configs:
        print("   - 继续使用有效的配置")
        print("   - 在NovAnything前端选择有效的模型配置")
    if invalid_configs:
        print("   - 检查无效配置的API Key和端点地址")
        print("   - 确认API Key的配额和权限设置")
        print("   - 对于火山引擎API，确认模型名称是否正确")
        print("   - 如果某个Key在服务中能用但测试失败，可能是网络环境差异")

    print("\n🔍 调试信息:")
    print("   - 如果测试结果与实际使用不符，请检查:")
    print("     1. 网络环境是否一致")
    print("     2. API Key是否在测试期间发生变化")
    print("     3. API提供商是否有地域限制")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消了测试")
    except Exception as e:
        print(f"\n\n💥 程序执行出错: {e}")
        print(f"🐛 完整错误信息:")
        print(traceback.format_exc()) 