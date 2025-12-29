"""
Mailprune CLI Entry Point

This module provides the main CLI entry point for the Mailprune application.
"""

import logging
import os

import click
from google_auth_oauthlib.flow import InstalledAppFlow

from mailprune.commands import (
    analyze_clusters,
    analyze_engagement,
    analyze_patterns,  # Updated from analyze_title_patterns_enhanced
    generate_report,
    perform_audit,
)
from mailprune.constants import (
    DEFAULT_CACHE_PATH,
    DEFAULT_CREDENTIALS_PATH,
    DEFAULT_MAX_EMAILS,
    DEFAULT_TOKEN_PATH,
    GMAIL_API_SCOPES,
)
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
    Mailprune - Email Audit and Analysis Tool

    Audit your Gmail inbox and identify noise patterns to improve email management.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)


@cli.command()
def auth() -> None:
    """
    Authenticate with Gmail API.

    Opens a browser to authorize the application and generates token.json
    for subsequent API access. Run this command first if you don't have a valid token.
    """
    if not os.path.exists(DEFAULT_CREDENTIALS_PATH):
        raise click.ClickException(
            f"❌ {DEFAULT_CREDENTIALS_PATH} not found!\n"
            "Please download your OAuth 2.0 credentials from Google Cloud Console\n"
            f"and save it as {DEFAULT_CREDENTIALS_PATH}"
        )

    if os.path.exists(DEFAULT_TOKEN_PATH):
        click.confirm(f"⚠️  {DEFAULT_TOKEN_PATH} already exists. Overwrite?", abort=True)

    click.echo("🔐 Starting authentication flow...")
    click.echo("Your browser will open for Google authorization.")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(DEFAULT_CREDENTIALS_PATH, GMAIL_API_SCOPES)
        creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open(DEFAULT_TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

        click.echo("✅ Authentication successful!")
        click.echo(f"Token saved to {DEFAULT_TOKEN_PATH}")
        click.echo("\nYou can now run: mailprune audit")
    except Exception as e:
        raise click.ClickException(f"Authentication failed: {e}")


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

    if audit_summary is None:
        raise click.ClickException("Failed to perform audit. Check that Gmail credentials are properly configured.")

    click.echo("Top 10 Noise Makers by Ignorance Score:")
    click.echo(audit_summary.head(10)[["from", "total_volume", "open_rate", "avg_recency_days", "ignorance_score"]].to_string(index=False))


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
@click.option("--brief", is_flag=True, help="Show brief summary instead of full report")
def report(csv_path: str, brief: bool):
    """Generate a comprehensive email audit and cleanup report."""
    generate_report(csv_path, brief)


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
@click.option("--use-nlp/--no-nlp", default=True, help="Use NLP for enhanced keyword extraction")
def patterns(cache_path: str, csv_path: str, top_n: int, by: str, use_nlp: bool):
    """Analyze content patterns for top senders using email snippets (by volume or ignorance score).

    Includes automatic intent inference using NLP to classify emails as promotional, transactional,
    informational, social, or unknown.
    """
    df = load_audit_data(csv_path)
    if df.empty:
        click.echo("No audit data found. Run 'mailprune audit' first.")
        return

    audit_data = df.to_dict("records")
    analyze_patterns(cache_path, audit_data, top_n, by, use_nlp)


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
@click.option("--tier", type=click.Choice(["high", "medium", "low", "zero", "all"]), default="all", help="Show detailed listing for specific engagement tier")
def engagement(csv_path: str, tier: str):
    """Analyze sender engagement patterns and tiers."""
    analyze_engagement(csv_path, tier)


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
@click.option("--n-clusters", default=5, type=int, help="Number of clusters to create (default: 5)")
def cluster(csv_path: str, n_clusters: int):
    """Analyze sender clusters for cleanup recommendations using unsupervised learning."""
    analyze_clusters(csv_path, n_clusters)
