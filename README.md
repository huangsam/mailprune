# Mailprune

Intelligent email management system that audits Gmail, identifies noise makers using data-driven analysis, and provides targeted cleanup strategies.

## Features

- **Email Auditing**: Comprehensive analysis of Gmail inbox with volume, open rates, and noise scoring
- **Noise Detection**: Identifies high-volume, low-engagement senders that contribute to inbox clutter
- **Cleanup Recommendations**: Provides actionable suggestions for unsubscribing and filtering
- **Progress Tracking**: Monitors cleanup effectiveness with baseline comparisons
- **Cache Pruning**: Automatically removes deleted emails from local cache between audit runs
- **Parallel Processing**: Uses service pool for concurrent Gmail API calls to speed up auditing
- **Title Pattern Analysis**: Analyzes email subject patterns for senders to understand content themes
- **CLI Tools**: Command-line interface for easy analysis and reporting

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
