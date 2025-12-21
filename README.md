# Mailprune

Intelligent email management system that audits Gmail, identifies noise makers using data-driven analysis, and provides targeted cleanup strategies.

## Features

- **Smart Email Auditing**: Analyzes Gmail inbox volume, open rates, and noise patterns to identify problematic senders
- **Targeted Cleanup**: Provides actionable recommendations for unsubscribing and filtering high-impact senders
- **Advanced Analysis**: Multiple analysis modes including engagement tiers, sender clustering and more
- **Performance Optimized**: Parallel processing and intelligent caching for fast, efficient audits
- **CLI Tools**: Command-line interface for comprehensive email management and reporting

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd mailprune

# Install dependencies
uv sync
```

## Usage

### Running an Email Audit

```bash
# Run a full email audit (requires Gmail API setup)
uv run python scripts/mailprune.py audit --max-emails 2000
```

### Analyzing Audit Results

```bash
# Generate comprehensive email audit and cleanup report
uv run python scripts/mailprune.py report

# Show email distribution summary and statistics
uv run python scripts/mailprune.py summary

# Analyze sender engagement patterns and tiers
uv run python scripts/mailprune.py engagement

# Show detailed listing of zero engagement senders
uv run python scripts/mailprune.py engagement --tier zero

# Perform unsupervised clustering analysis on senders
uv run python scripts/mailprune.py cluster

# Analyze specific sender
uv run python scripts/mailprune.py sender "newsletter@company.com"

# Analyze title patterns for top senders (by volume)
uv run python scripts/mailprune.py title-patterns --top-n 3

# Analyze title patterns for top problematic senders (by ignorance score)
uv run python scripts/mailprune.py title-patterns --by ignorance --top-n 5

# Analyze unread emails by Gmail categories
uv run python scripts/mailprune.py unread-by-category
```

## For AI Agents and Automated Tools

See [AGENTS.md](AGENTS.md) for detailed information about project structure, development workflows, testing, and guidelines for automated tools working with this codebase.
