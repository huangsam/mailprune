# Mailprune

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/huangsam/mailprune/ci.yml)](https://github.com/huangsam/mailprune/actions)
[![License](https://img.shields.io/github/license/huangsam/mailprune)](https://github.com/huangsam/mailprune/blob/main/LICENSE)

Smart email cleanup tool that audits your Gmail, spots noise makers, and suggests targeted fixes.

**Motivation:** Between huge sprints, my inbox inevitably ballooned to **900+** emails where I lost track of what mattered. Mailprune helped me—in a single day—drop that to under **100** emails and cut my subscription count from **~140** to **~100**.

## ✨ Features

- **Smart Auditing**: Analyzes inbox volume, open rates, and patterns
- **Targeted Cleanup**: Recommends unsubscribes and filters
- **Advanced Analysis**: Engagement tiers, clustering, and content patterns
- **Fast & Efficient**: Parallel processing with intelligent caching

## 🚀 Quick Start

1. **Install**: See [USERGUIDE.md](USERGUIDE.md) for detailed setup
2. **Set up Gmail API**: Follow [Google's guide], place `credentials.json` in `data/`
3. **Run Assessment**: `uv run mailprune audit --max-emails 2000`
4. **Get Recommendations**: `uv run mailprune report` and analyze results

[Google's guide]: https://developers.google.com/gmail/api/quickstart/python

## 📖 Usage

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
