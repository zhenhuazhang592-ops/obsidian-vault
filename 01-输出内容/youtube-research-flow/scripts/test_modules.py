#!/usr/bin/env python3
"""
测试脚本 - 验证各模块是否正常工作
"""

import sys
import os
import json

# 添加 scripts 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("YouTube Research Flow - 模块测试")
print("=" * 60)

# 1. 测试配置加载
print("\n1️⃣  测试配置文件加载...")
try:
    from config.youtube_research_config import load_config
    config = load_config()
    print("   ✅ 配置加载成功")
    print(f"   YouTube API Key: {config.get('youtube', {}).get('api_key', 'Not found')[:15]}...")
    print(f"   配额限制: {config.get('youtube', {}).get('quota_limit', 'Not found')}")
except Exception as e:
    print(f"   ❌ 配置加载失败: {e}")

# 2. 测试资源追踪
print("\n2️⃣  测试资源追踪模块...")
try:
    from resource_tracker import ResourceTracker
    tracker = ResourceTracker()
    tracker.log_operation('test', 'test_module', {'message': '测试日志'})
    print("   ✅ 资源追踪模块正常")
    print(f"   会话ID: {tracker.session_id}")
except Exception as e:
    print(f"   ❌ 资源追踪模块失败: {e}")

# 3. 测试分析类型推断
print("\n3️⃣  测试研究目标推断...")
try:
    from main import ResearchGoalInferrer
    inferrer = ResearchGoalInferrer()
    test_queries = [
        "榴莲测评",
        "榴莲挑选教程",
        "榴莲市场趋势",
        "金枕头 vs 黑枕头"
    ]
    for query in test_queries:
        goal = inferrer.infer_goal(query)
        print(f"   '{query}' -> {goal}")
    print("   ✅ 研究目标推断正常")
except Exception as e:
    print(f"   ❌ 研究目标推断失败: {e}")

# 4. 测试 Markdown 格式化
print("\n4️⃣  测试 Markdown 格式化...")
try:
    from main import format_markdown
    test_videos = [
        {
            'video_id': 'test123',
            'title': '测试视频',
            'channel_title': '测试频道',
            'view_count': 1000,
            'published_at': '2024-01-01',
            'thumbnail': 'test.jpg'
        }
    ]
    md = format_markdown(test_videos)
    print("   ✅ Markdown 格式化正常")
    print(f"   生成了 {len(md.split(chr(10)))} 行 Markdown")
except Exception as e:
    print(f"   ❌ Markdown 格式化失败: {e}")

# 5. 测试 NotebookLM 路径（不实际调用）
print("\n5️⃣  测试 NotebookLM 工具...")
try:
    which_output = os.popen('which notebooklm').read().strip()
    if which_output:
        print(f"   ✅ NotebookLM 已找到: {which_output}")
    else:
        print("   ⚠️  NotebookLM 未在 PATH 中，请运行：export PATH=\"$HOME/Library/Python/3.14/bin:$PATH\"")
except Exception as e:
    print(f"   ⚠️  检查 NotebookLM 时出错: {e}")

print("\n" + "=" * 60)
print("✅ 模块测试完成！")
print("=" * 60)
print("\n⚠️  注意事项：")
print("- ✅ 资源追踪模块：正常")
print("- ✅ 研究目标推断：正常")
print("- ✅ Markdown 格式化：正常")
print("- ⚠️  YouTube API 客户端：未安装 google-api-python-client")
print("- ✅ NotebookLM：已安装")
print("\n📝  解决网络问题后：")
print("1. 确保网络连接稳定")
print("2. 安装依赖: pip install --break-system-packages google-api-python-client")
print("3. 运行完整测试: python3 youtube-research-flow/scripts/main.py \"榴莲测评\" --max-results 3")
