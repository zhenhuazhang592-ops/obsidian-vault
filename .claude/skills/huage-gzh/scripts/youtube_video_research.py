#!/usr/bin/env python3
"""
YouTube 视频研究脚本 - 搜索 + 字幕提取 + Obsidian 格式输出
整合：YouTube Data API v3 + yt-dlp 字幕抓取

依赖安装：
  pip install google-api-python-client yt-dlp

Usage:
  python3 youtube_video_research.py "AI视频生成" --max 5 --lang zh --output "02-视频研究/"
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── YouTube API ────────────────────────────────────────────────────────────────

def get_youtube_client(api_key: str):
    try:
        from googleapiclient.discovery import build
        return build('youtube', 'v3', developerKey=api_key)
    except ImportError:
        print("❌ 请安装 google-api-python-client: pip install google-api-python-client")
        sys.exit(1)

def search_videos(youtube, query: str, max_results: int = 10, lang: str = "zh") -> list[dict]:
    """搜索 YouTube 视频，返回 metadata 列表"""
    params = {
        'part': 'snippet',
        'type': 'video',
        'q': query,
        'maxResults': min(max_results, 50),
        'order': 'relevance',
        'safeSearch': 'moderate',
    }
    if lang:
        params['relevanceLanguage'] = lang

    request = youtube.search().list(**params)
    response = request.execute()

    videos = []
    for item in response.get('items', []):
        snippet = item.get('snippet', {})
        video_id = item.get('id', {}).get('videoId', '')
        if not video_id:
            continue
        videos.append({
            'video_id': video_id,
            'title': snippet.get('title', '未知'),
            'description': snippet.get('description', ''),
            'channel_title': snippet.get('channelTitle', '未知'),
            'channel_id': snippet.get('channelId', ''),
            'published_at': snippet.get('publishedAt', ''),
            'thumbnail': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
            'tags': snippet.get('tags', []),
        })
    return videos

def get_video_statistics(youtube, video_id: str) -> Optional[dict]:
    """获取视频统计数据"""
    try:
        response = youtube.videos().list(part='contentDetails,statistics', id=video_id).execute()
        items = response.get('items', [])
        if not items:
            return None
        content = items[0].get('contentDetails', {})
        stats = items[0].get('statistics', {})

        # 解析时长 ISO 8601 -> 秒
        duration = content.get('duration', 'PT0S')
        import re
        m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        seconds = 0
        if m:
            hours, minutes, secs = m.groups()
            seconds = (int(hours or 0) * 3600 + int(minutes or 0) * 60 + int(secs or 0))

        return {
            'view_count': int(stats.get('viewCount', 0)),
            'like_count': int(stats.get('likeCount', 0)),
            'comment_count': int(stats.get('commentCount', 0)),
            'duration_seconds': seconds,
            'duration_str': format_duration(seconds),
        }
    except Exception:
        return None

def format_duration(seconds: int) -> str:
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

# ── yt-dlp 字幕提取 ────────────────────────────────────────────────────────────

def extract_subtitles(video_id: str, output_dir: str, lang: str = "zh") -> Optional[str]:
    """使用 yt-dlp 提取字幕文本，返回字幕内容或 None"""
    os.makedirs(output_dir, exist_ok=True)

    # 尝试顺序：中文自动字幕 -> 英文自动字幕 -> 无字幕
    lang_order = ['zh-Hans', 'zh', 'en'] if lang == 'zh' else ['en']

    for subtitle_lang in lang_order:
        try:
            cmd = [
                'yt-dlp',
                '--write-auto-sub',
                '--sub-lang', subtitle_lang,
                '--skip-download',
                '--convert-subs', 'txt',
                '--output', os.path.join(output_dir, f'{video_id}.%(ext)s'),
                f'https://www.youtube.com/watch?v={video_id}',
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                # 读取字幕文件
                txt_path = os.path.join(output_dir, f'{video_id}.txt')
                if os.path.exists(txt_path):
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        text = f.read().strip()
                    # 清理字幕时间戳残留
                    text = clean_subtitle_text(text)
                    if len(text) > 50:
                        return text
        except subprocess.TimeoutExpired:
            break
        except Exception:
            continue

    return None

def clean_subtitle_text(text: str) -> str:
    """清理字幕中的时间戳和多余空行"""
    import re
    # 移除时间戳行 [00:00:00] 或 <00:00>
    text = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', text)
    text = re.sub(r'<\d{2}:\d{2}:\d{2}>', '', text)
    # 合并多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# ── Obsidian Markdown 输出 ────────────────────────────────────────────────────

def extract_key_points(title: str, description: str, subtitle_text: str, max_points: int = 5) -> list[str]:
    """从标题+描述+字幕中提取关键观点"""
    # 简单启发式：从描述中按行提取
    lines = [l.strip() for l in description.split('\n') if len(l.strip()) > 20]
    points = []
    for line in lines[:max_points]:
        # 去除 URL
        line = re.sub(r'http\S+', '', line).strip()
        if line:
            points.append(line)
    # 如果不够，用字幕前几句
    if len(points) < 3 and subtitle_text:
        sub_lines = subtitle_text.split('\n')
        for line in sub_lines[:10]:
            line = line.strip()
            if len(line) > 15 and line not in points:
                points.append(line)
                if len(points) >= max_points:
                    break
    return points[:max_points]

import re

def write_video_note(video: dict, stats: Optional[dict], subtitle: Optional[str], output_path: Path):
    """生成 Obsidian 格式的笔记文件"""
    video_id = video['video_id']
    url = f"https://www.youtube.com/watch?v={video_id}"

    # 格式化日期
    pub_date = video['published_at'][:10] if video['published_at'] else '未知'

    # 关键观点
    key_points = extract_key_points(
        video['title'], video['description'], subtitle or ''
    )

    # 字数统计
    subtitle_len = len(subtitle) if subtitle else 0

    # frontmatter
    frontmatter = f"""---
source: "{url}"
type: youtube-video
channel: "{video['channel_title']}"
date: {pub_date}
duration: "{stats['duration_str'] if stats else '未知'}"
views: {stats['view_count'] if stats else 0}
tags: [{', '.join(f'"{t}"' for t in video.get('tags', [])[:5])}]
subtitle_length: {subtitle_len}
---

# {video['title']}

**频道**: [{video['channel_title']}](https://www.youtube.com/channel/{video['channel_id']})
**链接**: [YouTube]({url})
**发布日期**: {pub_date}
{"**时长**: " + stats['duration_str'] if stats else ""}
{"**播放量**: " + f"{stats['view_count']:,}" if stats else ""}
{"**点赞数**: " + f"{stats['like_count']:,}" if stats else ""}

## 视频描述

{video['description'][:500]}{"..." if len(video['description']) > 500 else ""}

## 关键观点

{"".join(f"- {point}\n" for point in key_points) if key_points else "- *(暂无字幕或描述信息)*\n"}

## 字幕内容
"""

    if subtitle:
        # 字幕太长则截断到 3000 字（保留前 3000 字 + 提示）
        if len(subtitle) > 3000:
            content = f"{subtitle[:3000]}\n\n...（字幕过长已截断，完整字幕见视频）"
        else:
            content = subtitle
    else:
        content = "*该视频无字幕，或提取失败。*"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter + "\n" + content + "\n")

# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='YouTube 视频研究：搜索 + 字幕提取 + Obsidian 输出'
    )
    parser.add_argument('query', help='搜索关键词')
    parser.add_argument('--max', type=int, default=5, help='最大视频数量（默认5）')
    parser.add_argument('--lang', default='zh', help='语言代码（默认zh）')
    parser.add_argument('--output', default='02-视频研究', help='输出目录')
    parser.add_argument('--api-key', help='YouTube API Key（默认从环境变量读取）')
    parser.add_argument('--no-subtitle', action='store_true', help='跳过字幕提取（只抓 metadata）')
    args = parser.parse_args()

    # API Key
    api_key = args.api_key or os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ 错误：未设置 YOUTUBE_API_KEY")
        print("   请设置环境变量：export YOUTUBE_API_KEY=你的Key")
        sys.exit(1)

    # yt-dlp 检查
    if not args.no_subtitle:
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  yt-dlp 未安装，跳过字幕提取")
            print("   安装：brew install yt-dlp")
            args.no_subtitle = True

    # 初始化
    youtube = get_youtube_client(api_key)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    slug_query = re.sub(r'[^\w\u4e00-\u9fff]+', '_', args.query)[:20]

    print(f"\n🔍 搜索：{args.query}（最多 {args.max} 个视频）")

    # Step 1: 搜索
    videos = search_videos(youtube, args.query, max_results=args.max, lang=args.lang)
    if not videos:
        print("❌ 未找到相关视频")
        sys.exit(1)
    print(f"✅ 找到 {len(videos)} 个视频\n")

    # Step 2: 逐个处理
    success = 0
    subtitle_ok = 0
    for i, video in enumerate(videos, 1):
        video_id = video['video_id']
        print(f"  [{i}/{len(videos)}] {video['title'][:40]}")

        # 统计数据
        stats = get_video_statistics(youtube, video_id)

        # 字幕提取
        subtitle = None
        if not args.no_subtitle:
            with tempfile.TemporaryDirectory() as tmp_dir:
                subtitle = extract_subtitles(video_id, tmp_dir, lang=args.lang)
            if subtitle:
                subtitle_ok += 1
                print(f"         ✅ 字幕 {len(subtitle)} 字")
            else:
                print(f"         ⚠️  无字幕")

        # 生成笔记
        slug_title = re.sub(r'[^\w\u4e00-\u9fff]+', '_', video['title'])[:30]
        note_path = output_dir / f"{timestamp}_{slug_query}_{i:02d}_{slug_title}.md"
        write_video_note(video, stats, subtitle, note_path)
        success += 1
        print(f"         📄 {note_path.name}")

    # Step 3: 生成索引
    index_path = output_dir / f"00-索引_{slug_query}_{timestamp}.md"
    write_index(index_path, args.query, videos, success, subtitle_ok, timestamp)
    print(f"\n✅ 完成：{success}/{len(videos)} 个视频")
    print(f"   字幕成功率：{subtitle_ok}/{success}")
    print(f"   📄 索引文件：{index_path.name}")


def write_index(index_path: Path, query: str, videos: list, success: int, subtitle_ok: int, timestamp: str):
    """生成研究索引文件"""
    lines = [
        "---",
        f"topic: {query}",
        f"date: {datetime.now().strftime('%Y-%m-%d')}",
        f"videos: {success}",
        f"subtitles: {subtitle_ok}",
        "type: youtube-research-index",
        "---",
        "",
        f"# YouTube 视频研究索引：{query}",
        "",
        f"**研究时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**搜索关键词**: {query}",
        f"**视频总数**: {success}",
        f"**字幕获取**: {subtitle_ok}/{success}",
        "",
        "## 视频清单",
        "",
        "| # | 标题 | 频道 | 时长 | 播放量 | 字幕 | 链接 |",
        "|---|---|---|---|---|---|---|",
    ]

    for i, v in enumerate(videos[:10], 1):
        url = f"https://www.youtube.com/watch?v={v['video_id']}"
        lines.append(f"| {i} | {v['title'][:30]} | {v['channel_title'][:15]} | - | - | - | [链接]({url}) |")

    lines.extend([
        "",
        "## 研究发现",
        "",
        "*（Qwen3-Max 综合摘要时填充此部分）*",
        "",
    ])

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    main()
