# MailPrune - Agent Documentation

This document provides information specifically for AI agents and automated tools working with the MailPrune codebase.

## Project Structure

```
mailprune/
├── src/mailprune/          # Core package
│   ├── __init__.py        # Package exports
│   ├── commands/          # CLI command implementations
│   │   ├── __init__.py   # Command package exports
│   │   ├── engagement.py # Engagement analysis command
│   │   ├── report.py     # Comprehensive report command
│   │   ├── summary.py    # Summary statistics command
│   │   ├── title_patterns.py # Title pattern analysis command
│   │   └── unread_by_category.py # Unread by category command
│   └── utils/             # Utility modules
│       ├── __init__.py   # Utils package exports
│       ├── analysis.py   # Email analysis functions
│       ├── audit.py      # Gmail API integration
│       ├── constants.py  # Constants and configuration
│       └── helpers.py    # General utility functions
├── scripts/               # Executable scripts
│   ├── __init__.py       # Package marker
│   └── mailprune.py      # Unified audit and analysis CLI
├── tests/                 # Test suite
│   ├── __init__.py       # Package marker
│   ├── test_analysis.py  # Analysis function tests
│   └── test_cli.py       # CLI command tests
├── data/                  # Data files and cache
│   ├── credentials.json  # Gmail API credentials
│   ├── email_cache.json  # Cached email metadata
│   ├── google-details.txt # Gmail API configuration
│   ├── noise_report.csv  # Generated audit results
│   └── token.json        # Gmail API authentication token
├── brainstorm/            # Development planning and notes
│   └── initial-plan.md   # Initial project planning document
├── pyproject.toml         # Project configuration and dependencies
├── uv.lock               # Dependency lock file
└── AGENTS.md             # This documentation
```

## Installation & Setup

```bash
# Clone the repository
git clone <repository-url>
cd mailprune

# Install dependencies
uv sync
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

## Key Files for Agents

### Core Modules
- `src/mailprune/utils/analysis.py` - Contains all analysis functions and metrics calculations
- `src/mailprune/utils/audit.py` - Gmail API integration and audit execution
- `src/mailprune/utils/constants.py` - Configuration constants and baseline metrics
- `src/mailprune/utils/helpers.py` - General utility functions for data loading and processing

### Command Modules
- `src/mailprune/commands/report.py` - Comprehensive email audit report generation
- `src/mailprune/commands/summary.py` - Email distribution summary statistics
- `src/mailprune/commands/engagement.py` - Sender engagement pattern analysis
- `src/mailprune/commands/title_patterns.py` - Title pattern analysis for senders
- `src/mailprune/commands/unread_by_category.py` - Unread email analysis by Gmail categories

### CLI Entry Points
- `scripts/mailprune.py` - Main unified CLI tool with all commands

### Data Files
- `data/noise_report.csv` - Generated audit results with sender metrics
- `data/email_cache.json` - Cached email metadata for analysis
- `data/credentials.json` - Gmail API credentials
- `data/token.json` - Gmail API authentication token
- `data/google-details.txt` - Additional Gmail API configuration details

## Agent Guidelines

### When Modifying Code
- Always run tests after changes: `uv run python -m pytest`
- Format code: `uv run ruff format`
- Lint code: `uv run ruff check --fix`
- Type check: `uv run mypy src/`

### When Adding Features
- Add corresponding tests in `tests/` directory
- Update type hints in function signatures
- Follow existing code patterns and naming conventions
- Update this documentation if project structure changes

### Data Dependencies
- Audit operations require Gmail API setup with valid credentials
- Analysis operations require existing `data/noise_report.csv` file
- Cache operations work with `data/email_cache.json` if present
