# Test fixtures and configuration
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ.setdefault("MCP_SERVER_KEY", "test-key-123")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")
os.environ.setdefault("JIMENG_API_KEY", "test-jimeng-key")
os.environ.setdefault("DIFY_WRITER_CACHE", tempfile.mkdtemp())


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary Obsidian vault with test articles."""
    vault = tmp_path / "vault"
    vault.mkdir()

    # Create test articles
    article1 = vault / "article1.md"
    article1.write_text("""---
tags: [test, tech]
date: 2024-01-01
---

# Test Article 1

这是一个测试文章。我们讨论了Python编程和人工智能技术。

但是实际上，我觉得这个主题非常有趣。不过需要更多的研究。

一、首先，我们来分析问题
二、然后，提出解决方案
三、最后，总结结论
""")

    article2 = vault / "article2.md"
    article2.write_text("""---
tags: [test, life]
date: 2024-01-02
---

# Test Article 2

生活不仅仅是代码。每天我们都在进步。

然后有一天回头看，发现已经走了很远。
""")

    article3 = vault / "article3.md"
    article3.write_text("""---
tags: [test, philosophy]
date: 2024-01-03
---

# Test Article 3

哲学让我们思考更深层次的问题。

因此，我们需要不断学习。根据研究表明，这是一个重要的发现。
""")

    return vault


@pytest.fixture
def temp_session_dir(tmp_path, monkeypatch):
    """Use temp directory for session state."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    monkeypatch.setenv("DIFY_WRITER_CACHE", str(tmp_path))
    return session_dir


@pytest.fixture
def auth_headers():
    """Auth headers for testing."""
    return {"X-MCP-Key": "test-key-123"}


@pytest.fixture
async def app_client():
    """Async HTTP client for app testing."""
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
