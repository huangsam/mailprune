# Mailprune

Intelligent email management system that audits Gmail, identifies noise makers using data-driven analysis, and provides targeted cleanup strategies.

## Features

- **Email Auditing**: Comprehensive analysis of Gmail inbox with volume, open rates, and noise scoring
- **Noise Detection**: Identifies high-volume, low-engagement senders that contribute to inbox clutter
- **Cleanup Recommendations**: Provides actionable suggestions for unsubscribing and filtering
- **Progress Tracking**: Monitors cleanup effectiveness with baseline comparisons
- **Cache Pruning**: Automatically removes deleted emails from local cache between audit runs
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
uv run python scripts/run_audit.py --max-emails 2000
```

### Analyzing Audit Results

```bash
# Generate comprehensive cleanup report
uv run python scripts/analyze_emails.py report

# Show top noise makers
uv run python scripts/analyze_emails.py top-noise --n 10

# Get overall email metrics
uv run python scripts/analyze_emails.py metrics

# Analyze specific sender
uv run python scripts/analyze_emails.py sender "newsletter@company.com"

# Show cleanup progress
uv run python scripts/analyze_emails.py progress
```

## Testing

Run the test suite:

```bash
# Run all tests
uv run python -m pytest

# Run with coverage
uv run python -m pytest --cov=src/mailprune

# Run specific test file
uv run python -m pytest tests/test_analysis.py
```

## Development

### Code Quality

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check --fix

# Type checking
uv run mypy src/
```

### Adding Tests

Tests are located in the `tests/` directory. Use pytest fixtures for test data and Click's test runner for CLI testing.

## Project Structure

```
mailprune/
├── src/mailprune/          # Core package
│   ├── __init__.py        # Package exports
│   ├── analysis.py        # Analysis functions
│   ├── audit.py          # Gmail API integration
│   ├── utils.py          # Utility functions
│   └── constants.py      # Constants and configuration
├── scripts/               # Executable scripts
│   ├── run_audit.py      # Audit runner
│   ├── analyze_emails.py # Analysis CLI
│   └── run_tests.py      # Test runner
├── tests/                 # Test suite
│   ├── test_analysis.py  # Analysis function tests
│   └── test_cli.py       # CLI command tests
└── data/                  # Data files and cache
```
