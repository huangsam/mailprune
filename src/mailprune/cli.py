"""
MailPrune CLI Entry Point

This module provides the main CLI entry point for the MailPrune application.
"""

import logging

import click

from mailprune.commands import (
    analyze_clusters,
    analyze_engagement,
    analyze_title_patterns_enhanced,
    analyze_unread_by_category,
    generate_report,
    perform_audit,
    show_summary,
)
from mailprune.constants import DEFAULT_CACHE_PATH, DEFAULT_MAX_EMAILS
from mailprune.utils import (
    analyze_sender_patterns,
    load_audit_data,
)

# Set up logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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
    default=DEFAULT_MAX_EMAILS,
    type=int,
    help=f"Maximum number of emails to audit (default: {DEFAULT_MAX_EMAILS})",
)
@click.option(
    "--query",
    default="-label:trash",
    help="Gmail search query to filter emails (default: -label:trash)",
)
@click.option(
    "--cache-path",
    default=str(DEFAULT_CACHE_PATH),
    help=f"Path to email cache file (default: {DEFAULT_CACHE_PATH})",
)
def audit(max_emails: int, query: str, cache_path: str) -> None:
    """
    Run email audit.

    Audits the last N emails from Gmail and generates a noise report
    identifying potential inbox clutter based on sender patterns and engagement.
    """
    if max_emails <= 0:
        raise click.BadParameter("max-emails must be a positive integer")

    logger.info(f"Running Phase 1 Audit with {max_emails} emails...")
    audit_summary = perform_audit(max_emails, query, cache_path)

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
@click.option("--cache-path", default=DEFAULT_CACHE_PATH, help=f"Path to email cache file (default: {DEFAULT_CACHE_PATH})")
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file (required for ignorance ranking)")
@click.option("--top-n", default=5, help="Number of top senders to analyze")
@click.option("--by", default="volume", type=click.Choice(["volume", "ignorance"]), help="Rank senders by volume or ignorance score")
@click.option("--use-nlp", default=True, type=bool, help="Use NLP for enhanced keyword extraction")
def title_patterns(cache_path: str, csv_path: str, top_n: int, by: str, use_nlp: bool):
    """Analyze title patterns for top senders (by volume or ignorance score)."""
    df = load_audit_data(csv_path)
    if df.empty:
        click.echo("No audit data found. Run 'mailprune audit' first.")
        return

    audit_data = df.to_dict("records")
    analyze_title_patterns_enhanced(cache_path, audit_data, top_n, by, use_nlp)


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


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
@click.option("--n-clusters", default=5, type=int, help="Number of clusters to create (default: 5)")
def cluster(csv_path: str, n_clusters: int):
    """Analyze sender clusters for cleanup recommendations using unsupervised learning."""
    analyze_clusters(csv_path, n_clusters)
