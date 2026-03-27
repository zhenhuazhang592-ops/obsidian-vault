---
name: youtube-research-flow
description: YouTube Research workflow that combines YouTube Data API search with NotebookLM for automated content research and analysis.
compatibility: Requires YouTube Data API v3 key, Google account for NotebookLM, and Python 3.8+
---

# YouTube Research Flow

A comprehensive workflow skill that searches YouTube using the official Data API v3, creates a NotebookLM notebook, imports video sources, performs intelligent analysis, and produces structured research outputs with deliverables.

## When to Use

Trigger this skill when user requests:
- "帮我研究这个主题" (Help me research this topic)
- "搜索YouTube上关于...的视频" (Search YouTube for videos about...)
- "做关于...的YouTube研究" (Do YouTube research on...)
- "分析这些YouTube视频..." (Analyze these YouTube videos...)
- Or explicitly mentions YouTube search + analysis workflow with NotebookLM

**Key phrases that should trigger:**
- YouTube 研究
- 视频分析
- 内容调研
- 主题探索

## Workflow Overview

```
┌─────────────────────────────────────────────────────┐
│ 1. YouTube Search                                    │
│    ↓                                           │
│ 2. NotebookLM Setup                               │
│    ↓                                           │
│ 3. Import Sources & Process                        │
│    ↓                                           │
│ 4. Analysis Generation                              │
│    ↓                                           │
│ 5. Create Deliverables (Optional)                 │
│    ↓                                           │
│ 6. Output Results                                 │
└─────────────────────────────────────────────────────┘
```

## Step 1: YouTube Search

Uses YouTube Data API v3 to search for relevant videos with comprehensive metadata.

### Features
- Search by topic with relevance scoring
- Filter by upload date (default: last 6 months)
- Filter by video duration
- Filter by view count
- Extract rich metadata for each video
- Calculate engagement metrics
- Sort by popularity, recency, or custom criteria

### Search Parameters

| Parameter | Default | Example |
|-----------|---------|----------|
| Topic | (required) | "榴莲测评" |
| Max Results | 10 | "show me 20 videos" |
| Time Range | 6 months | "last 3 months", "past year" |
| Duration Filter | any | "short videos", "videos > 10min" |
| Sort By | relevance | "most viewed", "most recent" |
| Research Goal | auto-inferred | "product reviews", "tutorials", "news analysis" |

### Output Format

For each video, returns:
- Video ID
- Title
- Channel name
- Channel ID
- Subscriber count
- View count
- Duration (formatted)
- Upload date (formatted)
- Like count
- Comment count
- Engagement ratio
- Video URL

### Research Goals

The skill automatically infers research goals from user input:
- **Product reviews**: "榴莲测评" → focus on review and comparison content
- **Tutorials**: "榴莲教程" → focus on educational content
- **News/Updates**: "榴莲新闻" → focus on recent news and announcements
- **Comparison**: "金枕头 vs 黑枕头" → focus on comparative analysis

## Step 2: NotebookLM Setup

Automatically creates a new NotebookLM notebook and configures it for the research workflow.

### Notebook Creation
- **Naming**: "YouTube Research: [topic] - [date]"
- **Structure**: Automatically organized with sections
- **Language**: Defaults to Chinese (zh_Hans), can override

### Notebook Sections

1. **Research Objective** - Records user's stated research goal and analysis direction
2. **Video Sources** - All imported YouTube videos with metadata
3. **Analysis Findings** - Main analysis results and insights
4. **Deliverables** - Optional generated artifacts (flashcards, infographics, etc.)
5. **Resource Log** - Tracks all YouTube API calls and NotebookLM operations

## Step 3: Import Sources & Process

Imports the YouTube search results into NotebookLM and waits for processing completion.

### Import Process

1. Add each video as a source
2. Include metadata in source notes
3. Wait for processing status to become "READY"
4. Handle errors gracefully

### Batch Import

Supports importing multiple videos at once:
- Progress tracking for each source
- Parallel processing when possible
- Error logging for failed imports

### Source Format

Each source is added with:
- Video URL
- Title
- Channel information
- Upload date
- View/Engagement metrics
- Research tags (auto-generated based on goals)

## Step 4: Analysis Generation

Performs intelligent analysis based on user's research goals and imported videos.

### Analysis Types

The skill generates different types of analysis based on the research goal:

#### For Product Reviews
- **Content Themes Analysis**
  - Common topics mentioned across videos
  - Sentiment analysis (positive/negative/neutral)
  - Product features highlighted

- **Comparative Analysis**
  - Direct comparison between products
  - Pros/cons summary
  - Price/quality correlation

- **Reviewer Credibility**
  - Top reviewers by subscriber count
  - Reviewer expertise level
  - Reviewer consistency patterns

#### For Tutorials/Educational
- **Teaching Quality Assessment**
  - Clarity of explanations
  - Production quality
  - Pace and structure
  - Use of visual aids

- **Content Coverage**
  - Breadth of topics covered
  - Depth of explanation
  - Beginner/intermediate/advanced levels

#### For News/Updates
- **Trend Analysis**
  - Popular topics and themes
  - Emerging trends
  - Seasonal patterns
  - Viral content identification

- **Credibility Assessment**
  - Channel authority score
  - Recency of content
  - Engagement quality

### Analysis Output

Results are organized into:
1. **Executive Summary** - Key insights at a glance
2. **Detailed Analysis** - In-depth findings by category
3. **Data Tables** - Structured tables for quick reference
4. **Visualizations** - When applicable (text-based charts)
5. **Recommendations** - Actionable insights

## Step 5: Create Deliverables (Optional)

Generates additional research artifacts based on analysis and user request.

### Deliverable Types

| Deliverable | Description | When Generated |
|-------------|-------------|------------------|
| Flashcards | Study aids for key concepts | Always if tutorials/educational |
| Infographic | Visual summary of findings | When user requests |
| Timeline | Chronological overview | For time-series data |
| Comparison Matrix | Side-by-side comparison | For product comparisons |
| Quiz | Assessment questions | When specified |
| Cheat Sheet | Quick reference guide | For tutorials |

### NotebookLM Artifact Types

The skill uses NotebookLM's generation capabilities:
- **Report**: "report" - Comprehensive written analysis
- **Flashcards**: "flashcards" - Study cards for memorization
- **Data Table**: "data-table" - Structured data tables
- **Mind Map**: "mind-map" - Hierarchical concept mapping
- **Quiz**: "quiz" - Knowledge testing
- **Infographic**: "infographic" - Visual information graphics

### Generation Control

Default: No deliverables (analysis only)
Override: Request specific deliverables via:
- "创建闪卡" (Create flashcards)
- "生成信息图表" (Create infographic)
- "生成时间线" (Create timeline)
- "生成测试" (Create quiz)

## Step 6: Output Results

Returns complete research results in structured Markdown format.

### Output Format

```markdown
# YouTube Research: [Topic]

## Research Objective

> [User's stated goal and analysis direction]

## Summary

[Executive summary with key insights]

## Video Sources

| # | Title | Channel | Views | Duration | Uploaded |
|---|--------|---------|-------|----------|----------|
| 1 | ... | ... | ... | ... | ... | ... |

## Analysis Findings

[Detailed analysis sections]

## Resource Log

[Metadata about all resources used]

## Development Notes

[Technical implementation details, optimizations, known issues]
```

### Content Sections

1. **Research Objective**: What was the research goal?
2. **User Intent**: What did the user want to know?
3. **Search Parameters**: What filters and criteria were applied?
4. **Analysis Type**: What kind of analysis was performed?
5. **Key Findings**: 3-5 main insights discovered
6. **Recommendations**: Action items based on findings
7. **Deliverables**: What artifacts were created?

### Resource Log

Tracks all API usage for transparency and debugging:

| Timestamp | Action | Resource | Details | Cost |
|-----------|--------|----------|--------|
| 2024-01-01 15:30:05 | YouTube API | Search: 10 videos | 100 quota units |
| 2024-01-01 15:30:10 | NotebookLM | Create notebook | - |
| 2024-01-01 15:35:20 | NotebookLM | Add 10 sources | - |
| 2024-01-01 15:40:30 | NotebookLM | Generate report | - |

## Development Notes

Any technical details about implementation, optimizations, or known issues.

## Installation & Configuration

### Prerequisites

1. **YouTube Data API Key**: Required for search functionality
   - Get from: https://console.cloud.google.com/apis/youtube/v3
   - Enable YouTube Data API v3
   - Create API key with appropriate quota

2. **Google Account**: Required for NotebookLM
   - Sign in to Google account linked to NotebookLM
   - Ensure access to NotebookLM features

3. **Python Dependencies**:
   ```bash
   pip install google-api-python-client google-auth-oauthlib
   ```

### API Key Configuration

Create a configuration file at `config/youtube_research_config.json`:

```json
{
  "youtube": {
    "api_key": "YOUR_YOUTUBE_API_KEY",
    "quota_limit": 10000,
    "max_results_per_day": 100
  },
  "notebooklm": {
    "default_language": "zh_Hans",
    "auto_create_deliverables": false,
    "default_notebook_name_template": "YouTube Research: {topic} - {date}"
  },
  "analysis": {
    "default_deliverables": [],
    "max_sources_per_analysis": 50
  }
}
```

### Setup Instructions

1. Create the config directory:
   ```bash
   mkdir -p youtube-research-flow/config
   ```

2. Set up your YouTube API key:
   ```bash
   # Edit config/youtube_research_config.json
   # Replace YOUR_YOUTUBE_API_KEY with your actual key
   ```

3. The skill will auto-detect the config file location

## Usage

### Basic Usage

```bash
# Search for 10 videos about 榴莲测评 from last 6 months
python3 youtube-research-flow/scripts/main.py "榴莲测评" --max-results 10 --months 6
```

### With Deliverables

```bash
# Search and create flashcards for the results
python3 youtube-research-flow/scripts/main.py "榴莲教程" --create-flashcards
```

### With Custom Analysis Direction

```bash
# Search and analyze as product reviews
python3 youtube-research-flow/scripts/main.py "金枕头 vs 黑枕头测评" --analysis-type comparison
```

### Specify Multiple Research Goals

```bash
# Search with explicit goals
python3 youtube-research-flow/scripts/main.py "榴莲市场趋势" \
  --goals "市场分析,产品对比,用户反馈"
```

## Parameters

| Short Flag | Full Flag | Description | Default |
|-------------|-----------|----------|----------|
| `-q` | `--query` | Research topic/query | Required |
| `-n` | `--max-results` | Number of videos | 10 |
| `-m` | `--months` | Time range in months | 6 |
| `-d` | `--duration-filter` | Duration filter | None |
| `-s` | `--sort-by` | Sort order | relevance |
| `-a` | `--analysis-type` | Analysis type | Auto-inferred |
| `--create-<deliverable>` | Create specific artifact | None |

### Deliverable Flags

Multiple deliverables can be specified:

```bash
# Create multiple deliverables
python3 youtube-research-flow/scripts/main.py "榴莲测评" \
  --create-flashcards \
  --create-infographic \
  --create-timeline
```

## Examples

### Example 1: Basic Product Research

**User**: "帮我研究榴莲测评视频"

**What happens**:
1. Searches YouTube for "榴莲测评" (auto-detects as product review goal)
2. Creates NotebookLM notebook
3. Imports top 10 videos
4. Generates comparative analysis report
5. Returns structured Markdown findings

### Example 2: Tutorial Research with Flashcards

**User**: "搜索榴莲挑选教程，创建闪卡"

**Command**:
```bash
python3 youtube-research-flow/scripts/main.py "榴莲挑选教程" --create-flashcards
```

**Result**:
- Notebook created with video sources
- Flashcards generated for each video
- Analysis organized by learning progression

### Example 3: Market Analysis with Infographic

**User**: "研究榴莲市场趋势，生成信息图表"

**Command**:
```bash
python3 youtube-research-flow/scripts/main.py "榴莲市场趋势" \
  --goals "市场分析,产品对比,用户反馈" \
  --create-infographic
```

**Result**:
- Comprehensive market analysis
- Visual infographic showing trends
- Competitive comparison matrix

### Example 4: Comparison Study

**User**: "对比金枕头和黑枕头测评视频"

**Command**:
```bash
python3 youtube-research-flow/scripts/main.py "金枕头 vs 黑枕头对比" \
  --analysis-type comparison
```

**Result**:
- Side-by-side comparison
- Pros/cons for each product
- Recommendation matrix

## Resource Tracking

All YouTube API calls and NotebookLM operations are logged for transparency and cost management.

### What's Tracked

- YouTube API quota usage
- Number of videos retrieved
- NotebookLM notebooks created
- Sources imported
- Analyses generated
- Deliverables created
- Errors and warnings

### Benefits

- **Cost Monitoring**: Track YouTube API costs (free tier has limits)
- **Audit Trail**: Complete record of all research activities
- **Debugging**: Identify patterns in failed operations
- **Optimization**: Understand which searches are most valuable

### Resource Log Format

```json
{
  "research_session_id": "2024-01-01-15-30-00",
  "youtube_api_calls": [
    {
      "operation": "search",
      "timestamp": "2024-01-01T15:30:05Z",
      "quota_used": 100,
      "results": 10
    }
  ],
  "notebooklm_operations": [
    {
      "operation": "create_notebook",
      "timestamp": "2024-01-01T15:30:10Z",
      "notebook_name": "YouTube Research: 榴莲测评 - 2024-01-01",
      "status": "success"
    },
    {
      "operation": "add_source",
      "timestamp": "2024-01-01T15:35:20Z",
      "source_type": "youtube_video",
      "status": "ready"
    }
  ],
  "analysis_results": [
    {
      "type": "comparative_analysis",
      "timestamp": "2024-01-01T15:40:15Z",
      "deliverables": ["report"],
      "findings_count": 5
    }
  ],
  "deliverables": [],
  "errors": []
}
```

## Error Handling

### Common Issues

1. **Missing YouTube API Key**
   - Error: "YouTube API key not found"
   - Solution: Add API key to config file
   - Logs resource as error but continues with fallback

2. **NotebookLM Authentication**
   - Error: "Not logged in to Google"
   - Solution: Run `notebooklm login`
   - Logs as non-fatal error

3. **Insufficient Quota**
   - Error: "YouTube API quota exceeded"
   - Solution: Use cached results, reduce max-results, or wait for quota reset

4. **Search Returns No Results**
   - Error: "No videos found matching criteria"
   - Solution: Suggest broader terms, longer time range, remove filters
   - Logs with warning, creates empty analysis with recommendations

5. **NotebookLM Rate Limits**
   - Error: "Too many requests to NotebookLM"
   - Solution: Implement exponential backoff, retry after delay
   - Logs with warning, shows retry count

### Recovery Mechanisms

The skill includes automatic recovery for transient errors:

- **Retry Logic**: Automatic retry with exponential backoff for rate limits
- **Fallback Mode**: If YouTube API fails, use stored research notes as base
- **Checkpoint Saving**: Saves progress to allow resumption from failures
- **Graceful Degradation**: Falls back to simpler analysis if full features unavailable

## Advanced Features

### Intelligent Research Goal Inference

The skill automatically infers research intent from user queries:

| Query Pattern | Inferred Goal | Analysis Type |
|--------------|---------------|---------------|
| "...测评" | product_reviews | Comparative analysis |
| "...教程" | tutorials | Educational assessment |
| "...教学" | tutorials | Teaching quality evaluation |
| "...趋势" | trends | Trend analysis and forecasting |
| "...对比" | comparison | Side-by-side comparison |
| "...市场" | market | Competitive landscape analysis |
| "...用户反馈" | user_feedback | Sentiment and pattern analysis |

### Multi-Session Support

Can run multiple research sessions in parallel:

```bash
# Research two topics concurrently
python3 youtube-research-flow/scripts/main.py "榴莲金枕" &
python3 youtube-research-flow/scripts/main.py "榴莲黑枕头"
```

Each session:
- Has unique session ID
- Creates separate NotebookLM notebook
- Generates independent reports
- No interference between sessions

### Persistent Knowledge Base

Optionally maintains a research knowledge base across sessions:

- Stores analysis results for future reference
- Can be queried for historical comparisons
- Supports incremental research updates

### Data Export Formats

Research results can be exported in multiple formats:

- **Markdown** (default): Structured document
- **JSON**: Machine-readable for integration
- **CSV**: Spreadsheet-compatible
- **PDF**: Professional report format

Use `--export-format` flag:

```bash
python3 youtube-research-flow/scripts/main.py "榴莲测评" --export-format csv
```

## Tips for Best Results

### Search Optimization

- Use specific, descriptive queries rather than broad terms
- Combine product names with review keywords
- Use date filters to focus on recent content
- Sort by view count for popular benchmarks, by date for trends

### Analysis Enhancement

- Define clear research objectives upfront
- Use multiple sources for comprehensive coverage
- Cross-reference findings from different videos/channels
- Look for patterns beyond surface-level data

### NotebookLM Tips

- NotebookLM has processing delays (can take 1-5 minutes per source)
- Use `--no-wait` for batch imports (process asynchronously)
- Check source status with `notebooklm source list` before generating analysis

### Deliverable Selection

Choose deliverables based on your goals:
- **Flashcards**: Best for learning and memorization
- **Infographics**: Best for presentations and social sharing
- **Reports**: Best for documentation and reference
- **Comparison Matrices**: Best for product comparisons
- **Mind Maps**: Best for complex topic relationships

## Limitations & Known Issues

### YouTube API Constraints

- Free tier: 10,000 units/day quota
- Search quota limits apply
- Rate limiting may affect large batch operations

### NotebookLM Constraints

- Rate limits on generation may apply
- Large notebooks with many sources may timeout
- Not all artifact types support batch creation

### Workarounds

- For quota issues: Implement caching, reduce max-results, schedule searches
- For rate limits: Use delays, batch operations during off-peak hours
- For large datasets: Process in smaller batches, use checkpoints

## Troubleshooting

### Configuration Issues

**Problem**: API key not recognized
- **Check**: Verify config file exists and is valid JSON
- **Test**: Run `python3 -c "from config import load_config; print(load_config())"`

**Problem**: NotebookLM command not found
- **Check**: Verify `notebooklm skill install` was run
- **Check**: PATH includes notebooklm binary: `which notebooklm`

### YouTube API Errors

**Invalid API Key**
```
Error: The request does not have valid authentication credentials.
```
- **Solution**: Regenerate API key in Google Console
- **Verify**: Key has YouTube Data API v3 enabled
```

**Quota Exceeded**
```
Error: The caller does not have permission to access this resource. Quota exceeded.
```
- **Solution**: Wait for quota reset (daily), reduce max-results
- **Monitor**: Check quota usage at https://console.cloud.google.com
```

### NotebookLM Errors

**Authentication Failed**
```
Error: Invalid credentials. Run notebooklm login.
```
- **Solution**: Run `notebooklm login` to re-authenticate
- **Check**: Internet connection, browser cookies valid
```

**Source Processing Timeout**
```
Warning: Source taking longer than expected.
```
- **Solution**: Increase timeout value or use `--no-wait` for batch
- **Workaround**: Process in smaller batches
```

## Version History

- **v1.0** - Initial release with basic workflow
  - YouTube Data API v3 integration
  - NotebookLM notebook creation
  - Basic analysis generation
  - Resource tracking

### Planned Enhancements

- **v1.1** - Advanced goal inference
  - Multi-goal research sessions
  - Persistent knowledge base
  - Additional deliverable types

- **v1.2** - Interactive mode
  - Chat-based research refinement
  - Real-time collaboration
  - Dynamic deliverable selection
