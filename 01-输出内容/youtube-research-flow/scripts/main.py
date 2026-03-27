#!/usr/bin/env python3
"""
YouTube Research Flow - Main Orchestrator
Combines YouTube Data API v3 search with NotebookLM for automated research and analysis.
"""

import sys
import os
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import Google API libraries
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"❌ 错误：无法导入 Google API 客户端库")
    print(f"   请运行: pip install google-api-python-client")
    print(f"   详细错误: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YouTubeResearcher:
    """Handles YouTube Data API v3 searches and metadata extraction"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = None
        self._init_youtube_client()

    def _init_youtube_client(self):
        """Initialize YouTube Data API v3 client"""
        try:
            # Build YouTube service with API key
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            logger.info("YouTube Data API v3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube client: {e}")
            raise

    def search_videos(
        self,
        query: str,
        max_results: int = 10,
        order: str = 'relevance',
        published_after: Optional[str] = None,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
        region_code: Optional[str] = None,
        relevance_language: Optional[str] = None,
        safe_search: bool = True
    ) -> List[Dict]:
        """
        Search YouTube using Data API v3

        Args:
            query: Search terms
            max_results: Maximum number of results to return (1-50)
            order: Order of results (relevance, date, viewCount, rating)
            published_after: Only return videos published after this date (format: YYYY-MM-DD)
            min_duration: Minimum video duration in seconds
            max_duration: Maximum video duration in seconds
            region_code: ISO 3166-1 alpha-2 country code (e.g., US, CN)
            relevance_language: Language code (e.g., zh, en)
            safe_search: Whether to filter potentially offensive content

        Returns:
            List of video metadata dictionaries
        """
        try:
            # Build search request
            search_params = {
                'part': 'snippet',
                'type': 'video',
                'q': query,
                'maxResults': min(max_results, 50),  # API limit
                'order': order,
                'safeSearch': safe_search
            }

            # Add optional filters
            if published_after:
                search_params['publishedAfter'] = published_after
            if min_duration:
                search_params['minDuration'] = f"{min_duration}s"
            if max_duration:
                search_params['maxDuration'] = f"{max_duration}s"
            if region_code:
                search_params['regionCode'] = region_code
            if relevance_language:
                search_params['relevanceLanguage'] = relevance_language

            # Execute search
            logger.info(f"Searching YouTube for: {query} (max: {max_results})")
            request = self.youtube.search().list(**search_params)

            # Process results
            videos = []
            for item in request:
                if item.id:
                    # Get video details
                    video_details = item.id
                    videos.append({
                        'video_id': video_details,
                        'title': item.snippet.title if item.snippet else 'Unknown',
                        'description': item.snippet.description if item.snippet else '',
                        'channel_id': item.snippet.channelId if item.snippet else None,
                        'channel_title': item.snippet.channelTitle if item.snippet else '',
                        'published_at': item.snippet.publishedAt.isoformat() if item.snippet.publishedAt else None,
                        'thumbnail': item.snippet.thumbnails.default.url if item.snippet.thumbnails else '',
                        'tags': [tag for tag in item.snippet.tags] if item.snippet.tags else []
                    })

            logger.info(f"Found {len(videos)} videos")
            return videos

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_video_statistics(self, video_id: str) -> Optional[Dict]:
        """Get detailed statistics for a video including engagement metrics"""
        try:
            # Get video statistics
            stats = self.youtube.videos().list(
                part='statistics',
                id=video_id
            )

            if not stats.items:
                logger.warning(f"No statistics found for video {video_id}")
                return None

            video_stats = stats.items[0].statistics

            return {
                'video_id': video_id,
                'view_count': video_stats.viewCount if video_stats.viewCount else 0,
                'like_count': video_stats.likeCount if video_stats.likeCount else 0,
                'comment_count': video_stats.commentCount if video_stats.commentCount else 0,
                'favorite_count': video_stats.favoriteCount if video_stats.favoriteCount else 0,
                'engagement_rate': self._calculate_engagement_rate(video_stats),
                'published_at': video_stats.publishedAt.isoformat() if video_stats.publishedAt else None
            }

        except Exception as e:
            logger.error(f"Failed to get statistics for {video_id}: {e}")
            return None

    def _calculate_engagement_rate(self, stats) -> float:
        """Calculate engagement rate (likes + comments) / views"""
        if not stats.viewCount or stats.viewCount == 0:
            return 0.0
        likes = stats.likeCount if stats.likeCount else 0
        comments = stats.commentCount if stats.commentCount else 0
        return round(((likes + comments) / stats.viewCount) * 100, 2)


class NotebookLMManager:
    """Manages NotebookLM operations via notebooklm-py CLI"""

    def __init__(self, notebooklm_path: str):
        self.notebooklm_path = notebooklm_path
        self._init_path()

    def _init_path(self):
        """Initialize notebooklm path and verify installation"""
        if self.notebooklm_path is None:
            # Try to find in PATH
            from shutil import which
            try:
                path = which('notebooklm')
                if path:
                    self.notebooklm_path = path
                    logger.info(f"Found notebooklm at: {path}")
            except:
                pass

        # Verify notebooklm is available
        if not self.notebooklm_path:
            logger.warning("notebooklm not found in PATH, will use system PATH")
            self.notebooklm_path = 'notebooklm'

        logger.info(f"Using notebooklm from: {self.notebooklm_path}")

    def create_notebook(self, name: str) -> tuple[bool, str]:
        """Create a new NotebookLM notebook"""
        try:
            logger.info(f"Creating notebook: {name}")
            import subprocess
            result = subprocess.run(
                [self.notebooklm_path, 'create', name],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            if result.returncode == 0:
                # Parse notebook ID from output
                for line in result.stdout.strip().split('\n'):
                    if 'Notebook ID:' in line:
                        notebook_id = line.split(':')[1].strip()
                        logger.info(f"Notebook created successfully: {notebook_id}")
                        return True, notebook_id
                    elif 'Error' in line:
                        logger.error(f"Failed to create notebook: {line}")
                        return False, f"Creation failed: {line}"

            error_msg = result.stderr.strip()
            if error_msg:
                logger.error(f"NotebookLM error: {error_msg}")
                return False, f"Creation failed: {error_msg}"

            return False, "Unknown error"

        except subprocess.TimeoutExpired:
            logger.error("NotebookLM creation timed out")
            return False, "Timeout"
        except subprocess.CalledProcessError as e:
            logger.error(f"NotebookLM creation failed: {e}")
            return False, f"Process failed: {e}"
        except Exception as e:
            logger.error(f"Unexpected error creating notebook: {e}")
            return False, f"Unexpected error: {e}"

    def import_source(self, notebook_id: str, source_path: str) -> bool:
        """Import a source file into NotebookLM notebook"""
        try:
            logger.info(f"Importing source: {source_path}")
            import subprocess
            result = subprocess.run(
                [self.notebooklm_path, 'source', 'add', '-n', notebook_id, source_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info(f"Source import initiated: {source_path}")
                return True
            else:
                error_msg = result.stderr.strip()
                logger.error(f"Source import failed: {error_msg}")
                return False

        except Exception as e:
            logger.error(f"Exception during source import: {e}")
            return False

    def wait_for_sources_ready(self, notebook_id: str, timeout: int = 300) -> bool:
        """Wait for all sources to be processed"""
        try:
            logger.info(f"Waiting for sources to be ready (timeout: {timeout}s)...")
            import time
            start_time = time.time()

            while True:
                result = subprocess.run(
                    [self.notebooklm_path, 'source', 'list', '-n', notebook_id],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10
                )

                all_ready = True
                for line in result.stdout.strip().split('\n'):
                    if 'READY' in line:
                        all_ready = all_ready and True
                    elif 'PROCESSING' in line:
                        all_ready = False
                    elif 'ERROR' in line:
                        logger.warning(f"Source error: {line}")

                if all_ready:
                    logger.info("All sources are ready")
                    return True

                elapsed = time.time() - start_time
                if elapsed > timeout:
                    logger.warning(f"Timeout after {timeout}s, not all sources ready")
                    return False

                time.sleep(5)

        except Exception as e:
            logger.error(f"Exception waiting for sources: {e}")
            return False

    def generate_analysis(
        self,
        notebook_id: str,
        prompt: str,
        deliverables: List[str] = []
    ) -> tuple[bool, str]:
        """Generate analysis content using NotebookLM"""
        try:
            logger.info(f"Generating analysis: {prompt}")

            # Build command
            cmd = [self.notebooklm_path, 'generate', 'report', '-n', notebook_id, prompt]

            # Add deliverables if specified
            for deliverable in deliverables:
                cmd.extend(['--create', deliverable])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info("Analysis generation initiated")
                return True, "Analysis started"
            else:
                error_msg = result.stderr.strip()
                logger.error(f"Analysis generation failed: {error_msg}")
                return False, f"Generation failed: {error_msg}"

        except Exception as e:
            logger.error(f"Exception during analysis generation: {e}")
            return False, f"Generation error: {e}"

    def download_results(self, notebook_id: str, output_filename: str) -> bool:
        """Download NotebookLM results to file"""
        try:
            logger.info(f"Downloading results to: {output_filename}")

            result = subprocess.run(
                [self.notebooklm_path, 'download', 'report', '-n', notebook_id, output_filename],
                capture_output=True,
                text=True,
                check=True,
                timeout=120
            )

            if result.returncode == 0:
                logger.info(f"Download completed: {output_filename}")
                return True
            else:
                error_msg = result.stderr.strip()
                logger.error(f"Download failed: {error_msg}")
                return False, f"Download failed: {error_msg}"

        except Exception as e:
            logger.error(f"Exception during download: {e}")
            return False, f"Download error: {e}"


class ResearchGoalInferrer:
    """Infers research goals from user queries"""

    REVIEW_KEYWORDS = ['测评', 'review', '评价', '对比', '测试', 'test', 'comparison', 'vs']
    TUTORIAL_KEYWORDS = ['教程', 'tutorial', '学习', '教学', 'educational', 'educational']
    TREND_KEYWORDS = ['趋势', 'trend', '市场', 'market', 'news', '新闻', '报道', 'update', '发布']
    USER_FEEDBACK_KEYWORDS = ['用户', '反馈', '评价', 'comments', '评论']

    @staticmethod
    def infer_from_query(query: str) -> str:
        """
        Infer research goal based on query content

        Returns:
            'product_reviews', 'tutorials', 'trends', 'market', 'user_feedback', or 'auto'
        """
        query_lower = query.lower()

        # Check for product review indicators
        for keyword in ResearchGoalInferrer.REVIEW_KEYWORDS:
            if keyword in query_lower:
                return 'product_reviews'

        # Check for tutorial indicators
        for keyword in ResearchGoalInferrer.TUTORIAL_KEYWORDS:
            if keyword in query_lower:
                return 'tutorials'

        # Check for trend/market keywords
        for keyword in ResearchGoalInferrer.TREND_KEYWORDS:
            if keyword in query_lower:
                return 'trends'

        # Check for user feedback
        for keyword in ResearchGoalInferrer.USER_FEEDBACK_KEYWORDS:
            if keyword in query_lower:
                return 'user_feedback'

        # Default to auto
        return 'auto'


class ResourceTracker:
    """Tracks all resource usage for debugging and cost monitoring"""

    def __init__(self, log_file: str = "resource_log.json"):
        self.log_file = log_file
        self.session_id = datetime.now().strftime("%Y%m%dT%H%M%S")
        self._init_log()

    def _init_log(self):
        """Initialize resource tracking log"""
        try:
            if os.path.exists(self.log_file):
                # Load existing log
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    try:
                        self.log_data = json.load(f)
                    except:
                        self.log_data = {"session_id": self.session_id, "operations": []}
            else:
                self.log_data = {
                    "session_id": self.session_id,
                    "operations": []
                }

            logger.info(f"Resource tracking initialized: {self.log_file}")

        except Exception as e:
            logger.warning(f"Failed to initialize resource log, starting fresh")
            self.log_data = {"session_id": self.session_id, "operations": []}

    def log_operation(self, operation_type: str, resource_type: str, details: Dict[str, Any]) -> None:
        """Log a resource operation"""
        operation = {
            "operation_type": operation_type,
            "resource_type": resource_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }

        self.log_data["operations"].append(operation)
        self._save_log()
        logger.debug(f"Logged: {operation_type} - {resource_type}")

    def _save_log(self):
        """Save resource tracking log"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.log_data, f, indent=2, ensure_ascii=False)
            logger.debug("Resource tracking log saved")
        except Exception as e:
            logger.error(f"Failed to save resource log: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of resource usage"""
        return {
            "session_id": self.session_id,
            "total_operations": len(self.log_data["operations"]),
            "youtube_api_calls": len([op for op in self.log_data["operations"] if op["resource_type"] == "youtube_api"]),
            "notebooklm_operations": len([op for op in self.log_data["operations"] if op["resource_type"] == "notebooklm"]),
            "videos_retrieved": sum(1 for op in self.log_data["operations"] if op["operation_type"] == "search" and op["details"].get("results_count", 0)),
            "analysis_generated": len([op for op in self.log_data["operations"] if op["operation_type"] == "analysis"]),
            "deliverables_created": len([op for op in self.log_data["operations"] if op["operation_type"] == "create_deliverable"])
        }

    def save_report(self, output_file: str) -> bool:
        """Save research results as markdown report"""
        try:
            # This will be implemented to save markdown output
            logger.info(f"Saving research report to: {output_file}")
            self.log_operation("save_report", "file", {"filename": output_file})
            return True
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return False


def load_config(config_path: str = "youtube-research-flow/config/youtube_research_config.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found: {config_path}")
            return {}

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.info(f"Loaded configuration from: {config_path}")
            return config

    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def format_markdown_summary(
    session_id: str,
    research_objective: str,
    goal_inference: str,
    videos: List[Dict],
    notebook_id: str,
    analysis_type: str,
    deliverables: List[str],
    resource_summary: Dict[str, Any]
) -> str:
    """Generate final markdown report"""

    lines = []
    lines.append(f"# YouTube Research: {research_objective}\n")
    lines.append(f"**研究目标**: {research_objective}\n")
    lines.append(f"**分析类型**: {goal_inference}\n")
    lines.append(f"**会话时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("---\n")

    # Research Objective section
    lines.append("## 研究目标\n")
    lines.append(f"{research_objective}\n")

    # Video Sources section
    lines.append("\n## 视频来源\n")
    lines.append("| # | 标题 | 频道 | 观看次数 | 时长 | 上传日期 |\n")
    lines.append("|---|------|--------|----------|----------|----------|---------|\n")

    for i, video in enumerate(videos, 1):
        title = video.get('title', '未知')[:40]
        channel = video.get('channel_title', '未知')[:20]
        views = video.get('view_count', 0)
        duration = video.get('published_at', '未知')

        lines.append(f"| {i} | {title} | {channel} | {views:,} | {duration} |\n")

    lines.append("\n## 分析发现\n")

    # Analysis Findings section will be populated by analysis
    lines.append("*[分析结果将在这里生成]*\n")

    # Deliverables section
    if deliverables:
        lines.append("\n## 可交付成果\n")
        for i, deliverable in enumerate(deliverables, 1):
            lines.append(f"- **{i}. {deliverable}**\n")
    lines.append(f"\n## 资源追踪\n")

    if resource_summary:
        lines.append("\n## 开发元数据\n")
        lines.append(f"- **YouTube API 调用次数**: {resource_summary.get('youtube_api_calls', 0)}\n")
        lines.append(f"- **检索视频总数**: {resource_summary.get('videos_retrieved', 0)}\n")
        lines.append(f"- **生成分析次数**: {resource_summary.get('analysis_generated', 0)}\n")
        lines.append(f"- **NotebookLM 操作次数**: {resource_summary.get('notebooklm_operations', 0)}\n")

    return '\n'.join(lines)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='YouTube Research Flow - Integrate YouTube Data API search with NotebookLM for automated research',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('query', help='研究主题/搜索词')
    parser.add_argument('--max-results', '-n', type=int, default=10,
                       help='最大结果数量 (1-50，默认：10)')
    parser.add_argument('--months', '-m', type=int, default=6,
                       help='时间范围（月），默认：6')
    parser.add_argument('--sort-by', '-s', choices=['relevance', 'date', 'viewCount'],
                       default='relevance', help='排序方式')
    parser.add_argument('--duration-min', '--min-dur', type=int,
                       help='最小时长（秒）')
    parser.add_argument('--duration-max', '--max-dur', type=int,
                       help='最大时长（秒）')
    parser.add_argument('--region', '-r', type=str,
                       help='地区代码（如 CN, US）')
    parser.add_argument('--analysis-type', '-a',
                       choices=['auto', 'product_reviews', 'tutorials', 'trends', 'market', 'user_feedback'],
                       default='auto', help='分析类型')
    parser.add_argument('--create-flashcards', '--flashcards', action='store_true',
                       help='创建闪卡')
    parser.add_argument('--create-infographic', '--infographic', action='store_true',
                       help='创建信息图表')
    parser.add_argument('--create-timeline', '--timeline', action='store_true',
                       help='创建时间线')
    parser.add_argument('--create-comparison', '--comparison', action='store_true',
                       help='创建对比矩阵')
    parser.add_argument('--create-quiz', '--quiz', action='store_true',
                       help='创建测试题')
    parser.add_argument('--create-cheatsheet', '--cheatsheet', action='store_true',
                       help='创建速查表')
    parser.add_argument('--no-deliverables', action='store_true',
                       help='不创建可交付成果')
    parser.add_argument('--export-format', choices=['markdown', 'json', 'csv'], default='markdown',
                       help='导出格式')
    parser.add_argument('--output-file', '-o', type=str,
                       help='输出文件路径')

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()

    # Setup
    config = load_config()
    api_key = config.get('youtube', {}).get('api_key')
    notebooklm_path = config.get('notebooklm', {}).get('path')

    if not api_key:
        print("❌ 错误：未配置 YouTube API Key")
        print("\n请按照以下步骤配置：")
        print("1. 访问 https://console.cloud.google.com/apis/youtube/v3")
        print("2. 创建或选择一个项目")
        print("3. 启用 YouTube Data API v3")
        print("4. 创建 API 密钥（凭据：OAuth 2.0 或服务账号）")
        print("5. 将 API 密钥添加到配置文件：")
        print("   config/youtube_research_config.json")
        print("6. 重新运行此命令")
        sys.exit(1)

    # Initialize managers
    try:
        yt_researcher = YouTubeResearcher(api_key)
        notebooklm_mgr = NotebookLMManager(notebooklm_path)
        goal_inferrer = ResearchGoalInferrer()
        resource_tracker = ResourceTracker()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        print(f"错误详情：{type(e).__name__}: {e}")
        sys.exit(1)

    # Infer analysis goal if not specified
    analysis_type = args.analysis_type
    if analysis_type == 'auto':
        analysis_type = goal_inferrer.infer_from_query(args.query)
        logger.info(f"Inferred analysis type: {analysis_type}")

    # Collect deliverables
    deliverables = []
    if args.create_flashcards:
        deliverables.append('flashcards')
    if args.create_infographic:
        deliverables.append('infographic')
    if args.create_timeline:
        deliverables.append('timeline')
    if args.create_comparison:
        deliverables.append('comparison_matrix')
    if args.create_quiz:
        deliverables.append('quiz')
    if args.create_cheatsheet:
        deliverables.append('cheatsheet')

    # Log session start
    resource_tracker.log_operation('session_start', 'session', {'query': args.query})

    # Step 1: YouTube Search
    print(f"\n🔍 步骤 1：搜索 YouTube 视频")
    print(f"   搜索词：{args.query}")
    print(f"   最大结果：{args.max_results}")
    print(f"   时间范围：最近 {args.months} 个月")
    print(f"   排序方式：{args.sort_by}")
    print(f"   分析类型：{analysis_type}\n")

    published_after = (datetime.now() - timedelta(days=args.months)).strftime('%Y-%m-%dT%H:%M:%S') if args.months > 0 else None

    # Build search parameters
    search_params = {
        'query': args.query,
        'max_results': args.max_results,
        'order': args.sort_by,
        'published_after': published_after
    }

    if args.duration_min:
        search_params['min_duration'] = args.duration_min
    if args.duration_max:
        search_params['max_duration'] = args.duration_max
    if args.region:
        search_params['region_code'] = args.region

    videos = yt_researcher.search_videos(**search_params)

    resource_tracker.log_operation('search', 'youtube_api', {
        'query': args.query,
        'results_count': len(videos),
        'params': search_params
    })

    if not videos:
        print("❌ 搜索失败：未找到相关视频")
        print("\n建议：")
        print("   • 使用更广泛的搜索词")
        print("   • 延长时间范围")
        print("   • 移除筛选条件")
        sys.exit(1)

    print(f"✅ 找到 {len(videos)} 个视频")

    # Step 2: NotebookLM Setup
    print(f"\n📓 步骤 2：创建 NotebookLM 笔记本")
    notebook_name = f"YouTube Research: {args.query} - {datetime.now().strftime('%Y-%m-%d')}"

    print(f"   笔记本名称：{notebook_name}")

    success, notebook_id = notebooklm_mgr.create_notebook(notebook_name)

    if not success:
        print(f"❌ NotebookLM 设置失败")
        sys.exit(1)

    print(f"✅ NotebookLM 笔记本已创建：{notebook_id}")
    resource_tracker.log_operation('create_notebook', 'notebooklm', {'notebook_name': notebook_name, 'notebook_id': notebook_id})

    # Step 3: Import Sources
    print(f"\n📥 步骤 3：导入视频源到 NotebookLM")

    imported_count = 0
    import_errors = 0

    for video in videos:
        source_note = (
            f"# 视频来源\n\n"
            "## 视频元数据\n"
            f"- **标题**: {video.get('title', '未知')}\n"
            f"- **频道**: {video.get('channel_title', '未知')}\n"
            f"- **视频ID**: {video.get('video_id')}\n"
            f"- **发布日期**: {video.get('published_at', '未知')}\n"
            f"- **观看次数**: {video.get('view_count', 0):,}\n"
            f"- **时长**: {video.get('published_at', '未知')}\n"
            f"- **链接**: https://www.youtube.com/watch?v={video.get('video_id')}\n\n"
            "## 内容描述\n"
            f"{video.get('description', '')}\n"
        )

        # Create temporary file with source note
        source_filename = f"temp_video_{video['video_id']}.md"

        with open(source_filename, 'w', encoding='utf-8') as f:
            f.write(source_note)

        # Import to NotebookLM
        success = notebooklm_mgr.import_source(notebook_id, source_filename)

        if success:
            imported_count += 1
            print(f"   ✅ 导入成功：{video.get('title', '未知')[:30]}")
        else:
            import_errors += 1
            print(f"   ❌ 导入失败：{video.get('title', '未知')[:30]}")

    resource_tracker.log_operation('add_source', 'notebooklm', {
        'video_id': video['video_id'],
        'title': video.get('title', '未知')[:30],
        'status': 'imported' if success else 'failed'
    })

    print(f"✅ 成功导入 {imported_count}/{len(videos)} 个视频源")

    # Step 4: Wait for Processing
    print(f"\n⏳ 步骤 4：等待视频处理完成")

    ready = notebooklm_mgr.wait_for_sources_ready(notebook_id, timeout=300)

    if not ready:
        print("❌ 视频处理超时")
        sys.exit(1)

    resource_tracker.log_operation('wait_sources', 'notebooklm', {'notebook_id': notebook_id, 'timeout': 300, 'status': 'success' if ready else 'timeout'})

    # Step 5: Generate Analysis
    print(f"\n🧠 步骤 5：生成分析")

    # Build analysis prompt based on goal and videos
    if analysis_type == 'product_reviews':
        prompt = (
            f"请分析这{len(videos)}个YouTube视频的榴莲测评内容。\n\n"
            f"你的任务是作为专业的榴莲测评专家，对这些视频进行深入分析。\n\n"
            "**重点要求**：\n"
            "1. **产品比较**：分析不同品牌/品种/规格/等级的榴莲\n"
            "2. **口感评估**：从标题、描述、标签中提取口感信息\n"
            "3. **用户体验分析**：评估视频的开箱体验、使用便利性\n"
            "4. **性价比分析**：价格与质量的对比\n"
            "5. **优缺点总结**：每个产品的优势和劣势\n\n"
            "**分析格式**：\n"
            "1. 为每个视频创建单独分析段落\n"
            "2. 提供清晰的对比表格\n"
            "3. 给出综合结论和建议\n"
            "4. 用客观、中性的语言\n\n"
            "**输出要求**：\n"
            "- 使用结构化的 Markdown 格式\n"
            "- 包含清晰的标题层级\n"
            "- 使用表格展示对比数据\n"
            "- 提供可操作的建议\n\n"
            "请开始分析。"
        )
    elif analysis_type == 'tutorials':
        prompt = (
            f"请分析这{len(videos)}个YouTube视频的榴莲教程/挑选内容。\n\n"
            "你的任务是作为榴莲知识专家，评估这些视频的教学价值。\n\n"
            "**重点要求**：\n"
            "1. **教学清晰度**：讲解是否清晰易懂\n"
            "2. **内容质量**：知识准确性、实用性\n"
            "3. **视觉呈现**：拍摄质量、图文清晰度\n"
            "4. **教学效果**：适合初学者还是进阶用户\n"
            "5. **实用性评估**：对实际购买和食用的指导价值\n\n"
            "**分析格式**：\n"
            "1. 为每个视频创建单独评估\n"
            "2. 识别教学要点和技巧\n"
            "3. 评估适合人群\n"
            "4. 提供改进建议\n\n"
            "**输出要求**：\n"
            "- 使用结构化的 Markdown 格式\n"
            "- 包含清晰的教学评分\n"
            "- 提供学习路径建议\n"
            "- 给出综合评估\n\n"
            "请开始分析。"
        )
    elif analysis_type == 'trends':
        prompt = (
            f"请分析这{len(videos)}个YouTube视频，揭示榴莲市场的最新趋势。\n\n"
            "你的任务是作为市场研究专家，识别并分析榴莲行业的趋势。\n\n"
            "**重点要求**：\n"
            "1. **热门品种趋势**：金枕头、黑枕头、猫山王、D24等的市场表现\n"
            "2. **消费趋势**：不同价位产品的受欢迎程度\n"
            "3. **地域偏好**：不同地区的榴莲消费习惯\n"
            "4. **季节性趋势**：榴莲品种的时令和供应情况\n"
            "5. **包装创新**：新的包装方式和营销策略\n\n"
            "**分析格式**：\n"
            "1. 识别主要的趋势模式\n"
            "2. 分析市场驱动因素\n"
            "3. 预测未来发展方向\n"
            "4. 提供市场机会洞察\n\n"
            "**输出要求**：\n"
            "- 使用结构化的 Markdown 格式\n"
            "- 包含清晰的趋势图表\n"
            "- 提供数据驱动的建议\n"
            "- 给出市场分析报告\n\n"
            "请开始分析。"
        )
    elif analysis_type == 'user_feedback':
        prompt = (
            f"请分析这{len(videos)}个YouTube视频的用户反馈和评价。\n\n"
            "你的任务是作为用户体验专家，分析用户关于榴莲产品的反馈。\n\n"
            "**重点要求**：\n"
            "1. **情感分析**：识别正面、负面和中性评论\n"
            "2. **关键问题**：提取用户最关心的问题（口感、品质、价格等）\n"
            "3. **用户画像**：分析用户群体特征\n"
            "4. **改进建议**：根据反馈提出产品和服务的改进方向\n\n"
            "**分析格式**：\n"
            "1. 分类用户反馈\n"
            "2. 统计满意度水平\n"
            "3. 识别高频问题\n"
            "4. 提供可行的改进方案\n\n"
            "**输出要求**：\n"
            "- 使用结构化的 Markdown 格式\n"
            "- 包含反馈统计表\n"
            "- 提供具体改进措施\n"
            "- 给出用户洞察总结\n\n"
            "请开始分析。"
        )
    else:
        prompt = (
            f"请分析这{len(videos)}个YouTube视频。\n\n"
            "你的任务是作为内容分析师，对视频进行全面分析。\n\n"
            "请根据视频标题、描述和标签，提供有价值的分析。\n\n"
            "**分析要点**：\n"
            "1. **内容概要**：视频的主要主题和目的\n"
            "2. **受众分析**：目标观众和内容定位\n"
            "3. **质量评估**：制作质量、信息价值\n"
            "4. **亮点识别**：视频中最有价值的部分\n"
            "5. **改进建议**：如何提升内容质量\n\n"
            "**输出要求**：\n"
            "- 使用结构化的 Markdown 格式\n"
            "- 包含清晰的标题层级\n"
            "- 提供实用的洞察\n"
            "- 使用列表组织内容\n\n"
            "请开始分析。"
        )

    # Add deliverables to prompt if specified
    if deliverables:
        deliverable_list = ", ".join(f" --create-{d}" for d in deliverables)
        prompt += f"\n\n**可交付成果**：在完成分析后，请生成以下可交付成果：{deliverable_list}。"
        prompt += "\n\n生成可交付成果的要求：\n- 内容简洁明了\n- 适合社交媒体分享\n- 包含关键发现和洞察\n- 使用视觉化元素（表格、图标等）\n"

    # Generate analysis
    print(f"   分析类型：{analysis_type}")
    print(f"   生成提示长度：{len(prompt)} 字符")

    success, result = notebooklm_mgr.generate_analysis(notebook_id, prompt, deliverables)

    if not success:
        print(f"❌ 分析生成失败：{result}")
        sys.exit(1)

    resource_tracker.log_operation('generate_analysis', 'notebooklm', {
        'analysis_type': analysis_type,
        'prompt_length': len(prompt),
        'deliverables': deliverables,
        'status': 'started' if success else 'failed'
    })

    print(f"✅ 分析已生成，等待完成...")

    # Step 6: Wait and Download
    print(f"\n⏳ 步骤 6：等待分析完成并下载结果")

    # Wait for completion (NotebookLM doesn't provide async status, so we'll wait a reasonable time)
    import time
    time.sleep(60)  # Wait 60 seconds for generation

    # Download results
    output_file = args.output_file if args.output_file else f"youtube_research_{args.query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    success = notebooklm_mgr.download_results(notebook_id, output_file)

    if not success:
        print(f"❌ 下载失败：{success}")
        sys.exit(1)

    resource_tracker.log_operation('download_report', 'file', {'filename': output_file, 'status': 'completed' if success else 'failed'})

    # Step 7: Generate Final Report
    final_report = format_markdown_summary(
        session_id=resource_tracker.session_id,
        research_objective=args.query,
        goal_inference=analysis_type,
        videos=videos,
        notebook_id=notebook_id,
        analysis_type=analysis_type,
        deliverables=deliverables,
        resource_summary=resource_tracker.get_summary()
    )

    # Save final report
    save_success = resource_tracker.save_report(output_file)

    if not save_success:
        print(f"❌ 报告保存失败：{save_success}")

    # Print final summary
    print(f"\n{'='*80}\n")
    print(f"🎉 YouTube Research 完成！\n")
    print(f"{'='*80}\n")
    print(f"📊 资源追踪：\n")
    summary = resource_tracker.get_summary()
    print(f"   会话ID：{summary['session_id']}")
    print(f"   YouTube API 调用：{summary['youtube_api_calls']}")
    print(f"   视频检索：{summary['videos_retrieved']} 个")
    print(f"   分析生成：{summary['analysis_generated']} 次")
    print(f"   NotebookLM 操作：{summary['notebooklm_operations']} 次")
    print(f"   可交付成果：{len(deliverables)} 个")
    print(f"{'='*80}\n")
    print(f"📄 结果文件：{output_file}")
    print(f"{'='*80}\n")

    # Open report in Obsidian if requested
    if args.output_file.startswith("youtube_research_"):
        try:
            print(f"📖 在 Obsidian 中打开：{output_file}")
            subprocess.run(['open', output_file], check=True)
        except:
            pass


if __name__ == "__main__":
    main()
