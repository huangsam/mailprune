#!/usr/bin/env python3
"""
Script to run Phase 1: Email Audit
This script performs the audit of the last N emails and generates a noise report.
"""

import logging
import sys
from pathlib import Path

import click

# Set up logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add the src directory to the path so we can import mailprune
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from mailprune.audit import perform_audit  # noqa: E402


@click.command()
@click.option(
    "--max-emails",
    "-n",
    default=2000,
    type=int,
    help="Maximum number of emails to audit (default: 2000)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(max_emails: int, verbose: bool) -> None:
    """
    Run Phase 1 Email Audit.

    This command audits the last N emails from Gmail and generates a noise report
    identifying potential inbox clutter based on sender patterns and engagement.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    if max_emails <= 0:
        raise click.BadParameter("max-emails must be a positive integer")

    logger.info(f"Running Phase 1 Audit with {max_emails} emails...")
    audit_summary = perform_audit(max_emails)

    if audit_summary is not None:
        click.echo("Top 10 Noise Makers by Ignorance Score:")
        click.echo(audit_summary.head(10)[["from", "total_volume", "open_rate", "avg_recency_days", "ignorance_score"]].to_string(index=False))


if __name__ == "__main__":
    main()
