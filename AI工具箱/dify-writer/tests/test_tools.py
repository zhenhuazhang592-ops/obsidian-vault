# Tests: safe_json_parse
import pytest

from app.core.utils import safe_json_parse, extract_json_from_text


class TestSafeJsonParse:
    """Tests for safe_json_parse (Eng Review: 2-retry fallback)."""

    def test_direct_parse(self):
        """Test direct valid JSON parsing."""
        data = {"key": "value", "num": 42}
        result = safe_json_parse('{"key": "value", "num": 42}')
        assert result == data

    def test_markdown_fence_stripped(self):
        """Test JSON with markdown code fences."""
        content = '```json\n{"key": "value"}\n```'
        result = safe_json_parse(content)
        assert result == {"key": "value"}

    def test_trailing_comma_removed(self):
        """Test JSON with trailing commas (common LLM mistake)."""
        content = '{"key": "value", "num": 42,}'
        result = safe_json_parse(content)
        assert result == {"key": "value", "num": 42}

    def test_fallback_returns_text(self):
        """Test invalid JSON returns text field."""
        content = "This is not JSON at all"
        result = safe_json_parse(content)
        assert result == {"text": content}

    def test_empty_string(self):
        """Test empty string returns empty text."""
        result = safe_json_parse("")
        assert result == {"text": ""}

    def test_whitespace_only(self):
        """Test whitespace-only returns empty text."""
        result = safe_json_parse("   \n\t  ")
        assert result == {"text": ""}

    def test_nested_json_with_markdown(self):
        """Test nested JSON with markdown fences."""
        content = '```json\n{"outer": {"inner": "value"}}\n```'
        result = safe_json_parse(content)
        assert result == {"outer": {"inner": "value"}}


class TestExtractJsonFromText:
    """Tests for extract_json_from_text."""

    def test_extract_from_mixed_text(self):
        """Test extracting JSON from explanatory text."""
        text = "Here is the result: {\"key\": \"value\"}. That's all."
        result = extract_json_from_text(text)
        assert result == {"key": "value"}

    def test_no_json_returns_none(self):
        """Test no JSON object found returns None."""
        text = "This is plain text without any JSON"
        result = extract_json_from_text(text)
        assert result is None

    def test_nested_braces(self):
        """Test nested braces extraction."""
        text = 'Start {"outer": {"inner": [1, 2, 3]}} end'
        result = extract_json_from_text(text)
        assert result == {"outer": {"inner": [1, 2, 3]}}


class TestHealthTool:
    """Tests for health tool."""

    def test_health_returns_status(self):
        """Test health tool returns healthy status."""
        from app.tools.health import HealthTool

        tool = HealthTool()
        result = tool.execute()

        assert result["status"] == "healthy"
        assert "uptime_seconds" in result
        assert "cpu_percent" in result
        assert "memory_mb" in result
        assert "pid" in result
        assert "timestamp" in result


class TestCheckQualityTool:
    """Tests for check_quality tool."""

    def test_short_article_low_score(self):
        """Test short article gets low quality score."""
        from app.tools.check_quality import CheckQualityTool

        tool = CheckQualityTool()
        result = tool.execute(article="这是一篇很短的公众号文章。")

        assert result["quality_score"] == 0.0
        assert len(result["issues"]) > 0

    def test_good_article_high_score(self):
        """Test well-structured article gets high score."""
        from app.tools.check_quality import CheckQualityTool

        tool = CheckQualityTool()
        # Create a proper-length article
        article = "一、首先，我们需要理解问题的本质。\n\n二、其次，分析原因。\n\n三、最后，提出解决方案。\n\n? 这是什么问题？"
        article = article * 50  # Make it long enough

        result = tool.execute(article=article, framework="清单型")

        assert result["quality_score"] > 50
        assert "issues" in result
        assert "suggestions" in result

    def test_empty_article(self):
        """Test empty article returns zero."""
        from app.tools.check_quality import CheckQualityTool

        tool = CheckQualityTool()
        result = tool.execute(article="")

        assert result["quality_score"] == 0.0


class TestFormatHtmlTool:
    """Tests for format_html tool."""

    def test_format_produces_html(self):
        """Test article is formatted as HTML."""
        from app.tools.format_html import FormatHtmlTool

        tool = FormatHtmlTool()
        article = "第一段内容。\n\n第二段内容。"
        result = tool.execute(article=article)

        assert "<!DOCTYPE html>" in result["html_string"]
        assert "第一段内容" in result["html_string"]
        assert result["status"] == "success"
        assert result["word_count"] == len(article)

    def test_format_with_images(self):
        """Test HTML includes images."""
        from app.tools.format_html import FormatHtmlTool

        tool = FormatHtmlTool()
        article = "第一段内容。"
        images = ["https://example.com/cover.jpg"]
        result = tool.execute(article=article, images=images)

        assert result["image_count"] == 1
        assert "cover.jpg" in result["html_string"]


class TestRecordPerformanceTool:
    """Tests for record_performance tool (stub)."""

    def test_record_writes_json(self, tmp_path):
        """Test performance metrics are written to JSON."""
        from app.tools.record_performance import RecordPerformanceTool

        tool = RecordPerformanceTool()
        metrics = {"views": 1000, "shares": 50}
        result = tool.execute(article_id="test-123", metrics=metrics)

        assert result["status"] == "recorded"
        assert result["article_id"] == "test-123"
        assert "file" in result


class TestGenerateCoverTool:
    """Tests for generate_cover tool (stub)."""

    def test_stub_returns_no_path(self):
        """Test stub returns None for local_image_path."""
        from app.tools.generate_cover import GenerateCoverTool

        tool = GenerateCoverTool()
        result = tool.execute(spec={"title": "Test"})

        assert result["status"] == "stub"
        assert result["local_image_path"] is None


class TestGenerateInlineImagesTool:
    """Tests for generate_inline_images tool (stub)."""

    def test_stub_returns_empty_paths(self):
        """Test stub returns empty list."""
        from app.tools.generate_inline_images import GenerateInlineImagesTool

        tool = GenerateInlineImagesTool()
        result = tool.execute(article="Test article content")

        assert result["status"] == "stub"
        assert result["local_paths"] == []
        assert result["count"] == 0


class TestAdaptToXHSTool:
    """Tests for adapt_to_xhs tool (stub)."""

    def test_stub_adapts_content(self):
        """Test stub adds XHS marker."""
        from app.tools.adapt_to_xhs import AdaptToXHSTool

        tool = AdaptToXHSTool()
        result = tool.execute(wechat_article="这是一篇很长的公众号文章。" * 20)

        assert result["status"] == "stub"
        assert "XHS" in result["xhs_content"]
        assert result["xhs_url"] is None
        assert result["cover_spec"]["width"] == 1242
        assert result["cover_spec"]["height"] == 1660


class TestMonitorObsidianTopicsTool:
    """Tests for monitor_obsidian_topics tool."""

    def test_nonexistent_vault_returns_error(self):
        """Test nonexistent vault path returns error."""
        from app.tools.monitor_obsidian_topics import MonitorObsidianTopicsTool

        tool = MonitorObsidianTopicsTool()
        result = tool.execute(vault_path="/nonexistent/path")

        assert result["status"] == "error"
        assert result["suggestions"] == []


class TestDeepResearchTool:
    """Tests for deep_research tool with concurrent search."""

    @pytest.mark.asyncio
    async def test_empty_queries_uses_topic(self):
        """Test empty queries list uses topic as query."""
        from app.tools.deep_research import DeepResearchTool

        tool = DeepResearchTool()
        result = await tool.execute(topic="AI研究", queries=[])

        assert result["topic"] == "AI研究"
        assert len(result["queries"]) == 1
        assert result["queries"][0] == "AI研究"

    @pytest.mark.asyncio
    async def test_multiple_queries_concurrent(self):
        """Test multiple queries run concurrently."""
        from app.tools.deep_research import DeepResearchTool

        tool = DeepResearchTool()
        queries = ["Python教程", "JavaScript教程", "Rust教程"]
        result = await tool.execute(topic="编程语言", queries=queries)

        assert len(result["sources"]) == 3
        assert result["source_count"] == 3

    @pytest.mark.asyncio
    async def test_mock_mode_without_api_key(self, monkeypatch):
        """Test mock mode when no API key."""
        import os

        monkeypatch.setenv("TAVILY_API_KEY", "")
        from app.tools.deep_research import DeepResearchTool

        tool = DeepResearchTool()
        result = await tool.execute(topic="测试", queries=["测试查询"])

        # Should return mock data
        assert result["sources"][0]["status"] == "mock"
        assert "测试查询" in result["sources"][0]["query"]

    @pytest.mark.asyncio
    async def test_research_summary_generated(self):
        """Test research summary is generated."""
        from app.tools.deep_research import DeepResearchTool

        tool = DeepResearchTool()
        result = await tool.execute(topic="AI", queries=["AI发展"])

        assert "summary" in result
        assert "source_count" in result


class TestExtractAuthorStyleTool:
    """Tests for extract_author_style tool."""

    def test_insufficient_articles_returns_defaults(self):
        """Test n < 3 returns default values."""
        from app.tools.extract_author_style import ExtractAuthorStyleTool

        tool = ExtractAuthorStyleTool()
        result = tool.execute(vault_path="/fake/path", n=2)

        assert result["tone"] == "formal"
        assert result["avg_sentence_length"] == 25.0
        assert "_warning" in result
        assert "insufficient" in result["_warning"]

    def test_nonexistent_vault_returns_defaults(self, temp_vault):
        """Test nonexistent vault returns defaults."""
        from app.tools.extract_author_style import ExtractAuthorStyleTool

        tool = ExtractAuthorStyleTool()
        result = tool.execute(vault_path="/nonexistent", n=3)

        assert result["tone"] == "formal"
        assert "_warning" in result

    def test_extracts_tone(self, temp_vault):
        """Test tone detection from article content."""
        from app.tools.extract_author_style import ExtractAuthorStyleTool

        tool = ExtractAuthorStyleTool()
        result = tool.execute(vault_path=str(temp_vault), n=3)

        assert "tone" in result
        assert result["tone"] in ["formal", "casual", "sharp", "gentle"]

    def test_extracts_avg_sentence_length(self, temp_vault):
        """Test average sentence length is calculated."""
        from app.tools.extract_author_style import ExtractAuthorStyleTool

        tool = ExtractAuthorStyleTool()
        result = tool.execute(vault_path=str(temp_vault), n=3)

        assert "avg_sentence_length" in result
        assert isinstance(result["avg_sentence_length"], float)

    def test_extracts_emoji_density(self, temp_vault):
        """Test emoji density is calculated."""
        from app.tools.extract_author_style import ExtractAuthorStyleTool

        tool = ExtractAuthorStyleTool()
        result = tool.execute(vault_path=str(temp_vault), n=3)

        assert "emoji_density" in result
        assert result["emoji_density"] >= 0.0

    def test_extracts_favorite_phrases(self, temp_vault):
        """Test favorite phrases are extracted."""
        from app.tools.extract_author_style import ExtractAuthorStyleTool

        tool = ExtractAuthorStyleTool()
        result = tool.execute(vault_path=str(temp_vault), n=3)

        assert "favorite_phrases" in result
        assert isinstance(result["favorite_phrases"], list)

    def test_extracts_structure_preference(self, temp_vault):
        """Test structure preference is detected."""
        from app.tools.extract_author_style import ExtractAuthorStyleTool

        tool = ExtractAuthorStyleTool()
        result = tool.execute(vault_path=str(temp_vault), n=3)

        assert "structure_preference" in result
        assert result["structure_preference"] in ["list", "story", "mixed"]


class TestSessionState:
    """Tests for session state management (Eng Review: atomic write + error handling)."""

    @pytest.mark.asyncio
    async def test_create_session(self, temp_session_dir):
        """Test session creation."""
        from app.core.session import SessionState

        session = SessionState.create(topic="测试主题", platform="wechat")

        assert session.session_id is not None
        assert len(session.session_id) == 36  # UUID format
        assert session.state["topic"] == "测试主题"
        assert session.state["platform"] == "wechat"
        assert session.state["revisions"] == 0

    @pytest.mark.asyncio
    async def test_update_session_state(self, temp_session_dir):
        """Test updating session state fields."""
        from app.core.session import SessionState

        session = SessionState.create(topic="测试", platform="wechat")
        session.update(outline={"title": "大纲"}, quality_score=85.0)

        assert session.state["outline"] == {"title": "大纲"}
        assert session.state["quality_score"] == 85.0
        assert session.state["updated_at"] is not None

    @pytest.mark.asyncio
    async def test_write_checkpoint_atomic(self, temp_session_dir):
        """Test atomic checkpoint write (tmp + rename)."""
        from app.core.session import SessionState

        session = SessionState.create(topic="测试", platform="wechat")
        session.update(quality_score=90.0)
        session.write_checkpoint()

        # Verify file exists
        assert session.state_file.exists()

        # Verify content
        import json

        with open(session.state_file) as f:
            loaded = json.load(f)
        assert loaded["quality_score"] == 90.0
        assert loaded["topic"] == "测试"

    @pytest.mark.asyncio
    async def test_load_checkpoint(self, temp_session_dir):
        """Test loading checkpoint from disk."""
        from app.core.session import SessionState

        # Create and save
        session = SessionState.create(topic="测试", platform="wechat")
        session.update(quality_score=75.0)
        session.write_checkpoint()

        # Load
        loaded = SessionState.load(session.session_id)
        assert loaded is not None
        assert loaded.state["topic"] == "测试"
        assert loaded.state["quality_score"] == 75.0

    def test_checkpoint_write_failure_handling(self, temp_session_dir, monkeypatch):
        """Test checkpoint write failure raises RuntimeError (Eng Review: critical gap #1)."""
        import os
        from app.core.session import SessionState

        session = SessionState.create(topic="测试", platform="wechat")

        # Mock os.replace to simulate failure after tmp file is written
        original_replace = os.replace

        def failing_replace(src, dst):
            # Clean up the temp file first
            try:
                os.unlink(src)
            except OSError:
                pass
            raise OSError("Simulated disk full / permission error")

        monkeypatch.setattr(os, "replace", failing_replace)

        with pytest.raises(RuntimeError, match="Failed to write checkpoint"):
            session.write_checkpoint()

    @pytest.mark.asyncio
    async def test_nonexistent_session_load_returns_none(self):
        """Test loading nonexistent session returns None (valid UUID but no file)."""
        from app.core.session import SessionState

        # Use a valid UUID format that doesn't exist on disk
        result = SessionState.load("00000000-0000-0000-0000-000000000000")
        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_session_id_format_rejected(self):
        """Test path traversal attempt via malformed session_id raises ValueError."""
        from app.core.session import SessionState

        for malicious_id in [
            "../../../etc",
            "..\\..\\windows\\system32",
            "foo/../../../etc",
            "x" * 100,
            "",
        ]:
            with pytest.raises(ValueError, match="Invalid session_id format"):
                SessionState.load(malicious_id)

    @pytest.mark.asyncio
    async def test_load_corrupted_checkpoint_raises_runtimeerror(self, temp_session_dir):
        """Test corrupted JSON checkpoint raises RuntimeError."""
        from app.core.session import SessionState

        session = SessionState.create(topic="test", platform="wechat")
        session.write_checkpoint()
        # Corrupt the file
        with open(session.state_file, "w") as f:
            f.write("not valid json{ broken")
        with pytest.raises(RuntimeError, match="Failed to load checkpoint"):
            SessionState.load(session.session_id)


class TestToolRegistry:
    """Tests for tool registry."""

    def test_register_and_get_tool(self):
        """Test registering and retrieving a tool."""
        from app.tools.base import BaseTool, ToolRegistry

        class DummyTool(BaseTool):
            name = "dummy"
            description = "A dummy tool"

            async def execute(self, **kwargs):
                return {"result": "ok"}

        registry = ToolRegistry()
        registry.register(DummyTool())

        assert registry.has("dummy")
        assert registry.get("dummy").name == "dummy"

    def test_list_tools(self):
        """Test listing all registered tools."""
        from app.tools.base import get_registry

        registry = get_registry()
        tools = registry.list_tools()

        assert len(tools) >= 10
        tool_names = [t["name"] for t in tools]
        assert "deep_research" in tool_names
        assert "check_quality" in tool_names
        assert "format_html" in tool_names


class TestPromptsLoader:
    """Tests for prompts loader."""

    def test_load_nonexistent_prompt_raises(self):
        """Test loading nonexistent prompt raises FileNotFoundError."""
        from app.core.prompts import PromptsLoader

        loader = PromptsLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent_prompt")

    def test_render_substitutes_variables(self, tmp_path):
        """Test prompt rendering substitutes variables."""
        from app.core.prompts import PromptsLoader

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.md").write_text("Hello {{user_name}}, you are {{user_age}} years old.")

        loader = PromptsLoader(prompts_dir)
        rendered = loader.render("test", user_name="Alice", user_age="30")

        assert rendered == "Hello Alice, you are 30 years old."

    def test_cache_cleared_on_reload(self, tmp_path):
        """Test cache is cleared on reload."""
        from app.core.prompts import PromptsLoader

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        prompt_file = prompts_dir / "test.md"
        prompt_file.write_text("Version 1")

        loader = PromptsLoader(prompts_dir)
        assert loader.load("test") == "Version 1"

        # Update file
        prompt_file.write_text("Version 2")
        assert loader.load("test") == "Version 1"  # Cached

        # Reload
        loader.reload("test")
        assert loader.load("test") == "Version 2"
