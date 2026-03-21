#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 get_lark_messages 工具"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 加载环境变量
env_file = os.path.join(project_root, '.env')
if os.path.exists(env_file):
    from dotenv import load_dotenv
    load_dotenv(env_file)

from src.xagent.agents.tools.lark_messages import get_lark_messages


async def test_get_lark_messages():
    """测试获取飞书消息"""
    
    # 设置测试环境变量
    os.environ['CURRENT_CHAT_ID'] = 'oc_1f33979901b84f7f4036b9c501deb452'
    
    print("=" * 80)
    print("测试 1: 获取最近 10 条消息")
    print("=" * 80)
    
    try:
        result = await get_lark_messages(page_size=10)
        
        # 检查返回结果
        if result and hasattr(result, 'content'):
            content_blocks = result.content
            if content_blocks and len(content_blocks) > 0:
                text_block = content_blocks[0]
                
                # text_block 可能是字典或对象
                if isinstance(text_block, dict):
                    text = text_block.get('text', '')
                elif hasattr(text_block, 'text'):
                    text = text_block.text
                else:
                    print(f"\n❌ 测试失败：无法获取文本内容")
                    return False
                
                print(text)
                
                # 检查是否成功获取消息（非空表示成功）
                if text.strip():
                    print("\n✅ 测试成功：成功获取消息")
                    return True
                else:
                    print("\n❌ 测试失败：未获取到消息")
                    return False
            else:
                print(f"\n❌ 测试失败：content 为空")
                return False
        else:
            print(f"\n❌ 测试失败：result 没有 content 属性")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败：发生异常 - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_lark_messages_with_page_token():
    """测试使用 page_token 获取更多消息"""
    
    # 设置测试环境变量
    os.environ['CURRENT_CHAT_ID'] = 'oc_1f33979901b84f7f4036b9c501deb452'
    
    print("\n" + "=" * 80)
    print("测试 2: 获取最近 5 条消息，然后使用 page_token 获取更多")
    print("=" * 80)
    
    try:
        # 第一次请求
        result1 = await get_lark_messages(page_size=5)
        
        if result1 and hasattr(result1, 'content'):
            content_blocks = result1.content
            if content_blocks and len(content_blocks) > 0:
                text_block = content_blocks[0]
                
                # text_block 可能是字典或对象
                if isinstance(text_block, dict):
                    text = text_block.get('text', '')
                elif hasattr(text_block, 'text'):
                    text = text_block.text
                else:
                    print(f"\n❌ 测试失败：无法获取文本内容")
                    return False
                
                print("第一次请求结果：")
                print(text)
                
                # 检查是否有更多消息（通过检查是否有 page_token 提示）
                if "page_token" in text:
                    # 提取 page_token
                    import re
                    match = re.search(r'page_token="([^"]+)"', text)
                    if match:
                        page_token = match.group(1)
                        print(f"\n提取到 page_token: {page_token}")
                        
                        # 第二次请求
                        print("\n第二次请求...")
                        result2 = await get_lark_messages(page_size=5, page_token=page_token)
                        
                        if result2 and hasattr(result2, 'content'):
                            content_blocks2 = result2.content
                            if content_blocks2 and len(content_blocks2) > 0:
                                text_block2 = content_blocks2[0]
                                
                                # text_block 可能是字典或对象
                                if isinstance(text_block2, dict):
                                    text2 = text_block2.get('text', '')
                                elif hasattr(text_block2, 'text'):
                                    text2 = text_block2.text
                                else:
                                    print(f"\n❌ 测试失败：无法获取文本内容")
                                    return False
                                
                                print(text2)
                                print("\n✅ 测试成功：成功使用 page_token 获取更多消息")
                                return True
                
                print("\n✅ 测试成功：第一次请求成功（没有更多消息）")
                return True
                    
        print("\n❌ 测试失败")
        return False
            
    except Exception as e:
        print(f"\n❌ 测试失败：发生异常 - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_lark_messages_without_chat_id():
    """测试在没有 chat_id 的情况下的错误处理"""
    
    # 清除环境变量
    if 'CURRENT_CHAT_ID' in os.environ:
        del os.environ['CURRENT_CHAT_ID']
    
    print("\n" + "=" * 80)
    print("测试 3: 测试没有 chat_id 时的错误处理")
    print("=" * 80)
    
    try:
        result = await get_lark_messages(page_size=10)
        
        if result and hasattr(result, 'content'):
            content_blocks = result.content
            if content_blocks and len(content_blocks) > 0:
                text_block = content_blocks[0]
                
                # text_block 可能是字典或对象
                if isinstance(text_block, dict):
                    text = text_block.get('text', '')
                elif hasattr(text_block, 'text'):
                    text = text_block.text
                else:
                    print(f"\n❌ 测试失败：无法获取文本内容")
                    return False
                
                print(text)
                
                # 检查是否返回了正确的错误信息
                if "无法获取 chat_id" in text:
                    print("\n✅ 测试成功：正确返回了错误信息")
                    return True
                else:
                    print("\n❌ 测试失败：错误信息不正确")
                    return False
                    
        print("\n❌ 测试失败")
        return False
            
    except Exception as e:
        print(f"\n❌ 测试失败：发生异常 - {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("开始测试 get_lark_messages 工具\n")
    
    # 运行测试
    test1_passed = await test_get_lark_messages()
    test2_passed = await test_get_lark_messages_with_page_token()
    test3_passed = await test_get_lark_messages_without_chat_id()
    
    # 打印总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"测试 1 (获取最近 10 条消息): {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"测试 2 (使用 page_token 获取更多): {'✅ 通过' if test2_passed else '❌ 失败'}")
    print(f"测试 3 (没有 chat_id 时的错误处理): {'✅ 通过' if test3_passed else '❌ 失败'}")
    print("=" * 80)
    
    # 检查所有测试是否通过
    all_passed = test1_passed and test2_passed and test3_passed
    if all_passed:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
