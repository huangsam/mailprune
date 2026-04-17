# Mailprune - Agent Documentation

## Project Structure & Key Files
```
mailprune/
├── src/mailprune/         # Core package
│   ├── commands/         # Logic: audit, cluster, report, engagement, patterns
│   ├── mcp_server.py     # FastMCP Server (Entry: mailprune-mcp)
│   └── constants.py      # Config & Paths
├── data/                 # noise_report.csv, email_cache.json, token.json
└── AGENTS.md             # This file
```

## Setup & Testing
- **Install**: `uv sync --editable`
- **Quality**: `uv run ruff check --fix`, `uv run mypy src/`
- **Test Suite**: `uv run python -m pytest`
- **MCP Test**: `uv run pytest tests/test_mcp.py`

## MCP Capabilities
Exposed via `mailprune-mcp`.

### Tools
- `audit`: Fetch Gmail metadata & calculate Ignorance Scores. (Network I/O)
- `report`: Generate actionable cleanup summaries.
- `patterns`: NLP-driven content & intent analysis. (CPU Heavy)
- `engagement`: Categorize senders by interaction tiers.
- `cluster`: Unsupervised sender clustering.

### Resources
- `mailprune://guidance/cleanup-strategy`: Logic for interpreting results.
- `mailprune://guidance/noise-metrics`: Formula for Ignorance Score.

## Development Guidelines
- **Modifications**: Always run full test suite and verify MCP registration.
- **Dependencies**: Requires valid `credentials.json` in `data/` for audit operations.
- **Concurrency**: MCP tools use `anyio` for thread-safe blocking I/O offloading.
- **Standard**: Follow PEP 8 and existing async patterns in `mcp_server.py`.
