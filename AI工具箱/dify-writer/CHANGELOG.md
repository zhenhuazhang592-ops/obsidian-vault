# Changelog

## [0.1.0.0] - 2026-04-14

### Added
- MCP Server: FastAPI + SSE streaming on port 8080
- Session state management with atomic checkpoint writes
- 9 tools: deep_research, extract_author_style, check_quality, format_html, health, record_performance, generate_cover, generate_inline_images, adapt_to_xhs
- Path traversal protection via UUID validation on session_id
- Async-safe metrics recording with tempfile+rename
- Concurrent Tavily research with mock fallback
- 45 tests (43 existing + 2 new regression tests)

### Fixed
- Async blocking: _record_request now uses asyncio.to_thread
- Async blocking: session.write_checkpoint now uses asyncio.to_thread
- Session checkpoint OSError handling with proper cleanup
- Corrupted checkpoint JSON raises RuntimeError instead of silent None
