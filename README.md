# Mailprune

Intelligent email management system that audits Gmail, identifies noise makers using data-driven analysis, and provides targeted cleanup strategies.

## Features

- **Smart Email Auditing**: Analyzes inbox volume, open rates, and noise patterns
- **Targeted Cleanup**: Actionable recommendations for unsubscribing and filtering
- **Advanced Analysis**: Multiple modes including engagement tiers and clustering
- **Performance Optimized**: Parallel processing and intelligent caching
- **CLI Tools**: Command-line interface for email management and reporting

## Installation

```bash
# Clone the repository
gh repo clone huangsam/mailprune
cd mailprune

# Install dependencies
uv sync
```

## Usage

### Running an Email Audit

```bash
# Run a full email audit (requires Gmail API setup)
# Follow instructions at https://developers.google.com/gmail/api/quickstart/python
# Then place your credentials.json in the $REPO_ROOT/data directory
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

# Perform unsupervised clustering analysis on senders
uv run python scripts/mailprune.py cluster

# Analyze specific sender patterns
uv run python scripts/mailprune.py sender "newsletter@company.com"
```

Run `uv run python scripts/mailprune.py --help` for more commands and options.

## For AI Agents and Automated Tools

See [AGENTS.md](AGENTS.md) for detailed information about project structure, development workflows, testing, and guidelines for automated tools working with this codebase.
