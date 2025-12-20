# MailPrune - Agent Documentation

This document provides information specifically for AI agents and automated tools working with the MailPrune codebase.

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
│   ├── __init__.py       # Package marker
│   └── mailprune.py      # Unified audit and analysis CLI
├── tests/                 # Test suite
│   ├── __init__.py       # Package marker
│   ├── test_analysis.py  # Analysis function tests
│   └── test_cli.py       # CLI command tests
├── data/                  # Data files and cache
├── brainstorm/            # Development planning and notes
│   └── initial-plan.md   # Initial project planning document
└── pyproject.toml         # Project configuration and dependencies
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
- `src/mailprune/analysis.py` - Contains all analysis functions and metrics calculations
- `src/mailprune/audit.py` - Gmail API integration and audit execution
- `src/mailprune/constants.py` - Configuration constants and baseline metrics
- `src/mailprune/utils.py` - Utility functions for data loading and processing

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
