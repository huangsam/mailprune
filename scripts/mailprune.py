#!/usr/bin/env python3
"""
MailPrune - Email Audit and Analysis Tool

A comprehensive tool for auditing Gmail and identifying email noise patterns.
Combines audit execution and result analysis in a single interface.
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

from mailprune import (  # noqa: E402
    analyze_sender_patterns,
    load_audit_data,
    perform_audit,
)
from mailprune.commands import (  # noqa: E402
    analyze_engagement,
    analyze_title_patterns,
    analyze_unread_by_category,
    generate_report,
    show_summary,
)


@click.group()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def cli(verbose: bool):
    """
    MailPrune - Email Audit and Analysis Tool

    Audit your Gmail inbox and identify noise patterns to improve email management.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)


@cli.command()
@click.option(
    "--max-emails",
    "-n",
    default=2000,
    type=int,
    help="Maximum number of emails to audit (default: 2000)",
)
def audit(max_emails: int) -> None:
    """
    Run email audit.

    Audits the last N emails from Gmail and generates a noise report
    identifying potential inbox clutter based on sender patterns and engagement.
    """
    if max_emails <= 0:
        raise click.BadParameter("max-emails must be a positive integer")

    logger.info(f"Running Phase 1 Audit with {max_emails} emails...")
    audit_summary = perform_audit(max_emails)

    if audit_summary is not None:
        click.echo("Top 10 Noise Makers by Ignorance Score:")
        click.echo(audit_summary.head(10)[["from", "total_volume", "open_rate", "avg_recency_days", "ignorance_score"]].to_string(index=False))


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
def report(csv_path: str):
    """Generate a comprehensive email audit and cleanup report."""
    generate_report(csv_path)


@cli.command()
@click.argument("sender_name")
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
def sender(sender_name: str, csv_path: str):
    """Analyze a specific sender."""
    df = load_audit_data(csv_path)
    if df.empty:
        return

    sender_data = analyze_sender_patterns(df, sender_name)
    if sender_data:
        click.echo(f"=== 📧 {sender_data['sender']} ===")
        click.echo(f"Total Emails: {sender_data['total_emails']}")
        click.echo(f"Open Rate: {sender_data['open_rate']:.1f}%")
        click.echo(f"Ignorance Score: {sender_data['ignorance_score']:.0f}")
        click.echo(f"Unread Count: {sender_data['unread_count']}")
    else:
        click.echo(f"Sender '{sender_name}' not found in audit data.")


@cli.command()
@click.option("--cache-path", default="data/email_cache.json", help="Path to the email cache file")
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file (required for ignorance ranking)")
@click.option("--top-n", default=5, help="Number of top senders to analyze")
@click.option("--by", default="volume", type=click.Choice(["volume", "ignorance"]), help="Rank senders by volume or ignorance score")
def title_patterns(cache_path: str, csv_path: str, top_n: int, by: str):
    """Analyze title patterns for top senders (by volume or ignorance score)."""
    analyze_title_patterns(cache_path, csv_path, top_n, by)


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
def summary(csv_path: str):
    """Show email distribution summary and statistics."""
    show_summary(csv_path)


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
@click.option("--tier", type=click.Choice(["high", "medium", "low", "zero", "all"]), default="all", help="Show detailed listing for specific engagement tier")
def engagement(csv_path: str, tier: str):
    """Analyze sender engagement patterns and tiers."""
    analyze_engagement(csv_path, tier)


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
def unread_by_category(csv_path: str):
    """Analyze unread emails grouped by Gmail categories."""
    analyze_unread_by_category(csv_path)


if __name__ == "__main__":
    cli()
