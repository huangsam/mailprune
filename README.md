# Mailprune

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/huangsam/mailprune/ci.yml)](https://github.com/huangsam/mailprune/actions)
[![License](https://img.shields.io/github/license/huangsam/mailprune)](https://github.com/huangsam/mailprune/blob/main/LICENSE)

Smart email cleanup tool that audits your Gmail, spots noise makers, and suggests targeted fixes.

## 💡 Motivation

Between high-intensity work sprints, my personal digital organization often takes a backseat. Recently, my inbox hit a breaking point with **900+** unread messages, burying important threads under a mountain of junk.

Mailprune allowed me to execute a much-needed 'digital deep clean' in record time. In a single day, I whittled my inbox down to **under 100 emails** and audited my subscriptions—cutting them from **140** to **100**. It didn’t just clear the clutter; it fixed the source of the noise so the pileup doesn't happen again.

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
