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

# Install dependencies along with mailprune in editable mode
uv sync --editable

# Optional: Install NLP dependencies for enhanced content pattern analysis
uv sync --group nlp
```

## Usage

### Running an Email Audit

```bash
# Run a full email audit (requires Gmail API setup)
# Follow instructions at https://developers.google.com/gmail/api/quickstart/python
# Then place your credentials.json in the $REPO_ROOT/data directory
uv run mailprune audit --max-emails 2000
```

### Analyzing Audit Results

```bash
# Generate comprehensive email audit and cleanup report
uv run mailprune report

# Analyze sender engagement patterns and tiers
uv run mailprune engagement

# Perform unsupervised clustering analysis on senders
uv run mailprune cluster

# Analyze content patterns for top senders (with optional NLP)
uv run mailprune patterns --top-n 5 --by volume

# Analyze specific sender patterns
uv run mailprune sender "newsletter@company.com"
```

Run `uv run mailprune --help` for more commands and options.

## For AI Agents and Automated Tools

See [AGENTS.md](AGENTS.md) for detailed information about project structure, development workflows, testing, and guidelines for automated tools working with this codebase.
