# Mailprune

Smart email cleanup tool that audits your Gmail, spots noise makers, and suggests targeted fixes.

## ✨ Features

- **Smart Auditing**: Analyzes inbox volume, open rates, and patterns
- **Targeted Cleanup**: Recommends unsubscribes and filters
- **Advanced Analysis**: Engagement tiers, clustering, and content patterns
- **Fast & Efficient**: Parallel processing with intelligent caching

## 🚀 Quick Start

1. **Install**: `gh repo clone huangsam/mailprune; cd mailprune; uv sync --editable`
2. **Set up Gmail API**: Follow [Google's guide], place `credentials.json` in `data/`
3. **Run Assessment**: `uv run mailprune audit --max-emails 2000`
4. **Get Recommendations**: Follow [USERGUIDE.md](USERGUIDE.md) for full workflow

[Google's guide]: https://developers.google.com/gmail/api/quickstart/python

## 📖 Usage

### Streamlined Assessment
For guided cleanup with AI assistance, see [USERGUIDE.md](USERGUIDE.md).

### Manual Commands
```bash
# Audit inbox
uv run mailprune audit --max-emails 2000

# Generate report
uv run mailprune report

# Analyze engagement
uv run mailprune engagement

# Find patterns
uv run mailprune patterns --top-n 5 --by volume

# Cluster senders
uv run mailprune cluster
```

Run `uv run mailprune --help` for all options.

## 🤖 For AI Agents
See [AGENTS.md](AGENTS.md) for development details, testing, and automation guidelines.
