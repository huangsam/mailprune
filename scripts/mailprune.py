#!/usr/bin/env python3
"""
MailPrune - Email Audit and Analysis Tool

A comprehensive tool for auditing Gmail and identifying email noise patterns.
Combines audit execution and result analysis in a single interface.
"""

import json
import logging
import sys
from collections import Counter, defaultdict
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
    BASELINE_METRICS,
    analyze_sender_patterns,
    calculate_overall_metrics,
    generate_cleanup_report,
    get_top_noise_makers,
    load_audit_data,
)
from mailprune.audit import perform_audit  # noqa: E402


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
    """Generate a comprehensive cleanup report."""
    df = load_audit_data(csv_path)
    if df.empty:
        return

    report = generate_cleanup_report(df, BASELINE_METRICS)
    click.echo(report)


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
@click.option("--n", default=10, help="Number of top noise makers to show")
def top_noise(csv_path: str, n: int):
    """Show the top N noise makers."""
    df = load_audit_data(csv_path)
    if df.empty:
        return

    top_n = get_top_noise_makers(df, n)
    click.echo(f"=== 🏆 TOP {n} NOISE MAKERS ===")
    for i, (_, row) in enumerate(top_n.iterrows(), 1):
        click.echo(f"{i:2d}. {row['from']:<50} | Vol: {int(row['total_volume']):3d} | Open: {row['open_rate']:5.1f}% | Score: {row['ignorance_score']:6.0f}")


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
def metrics(csv_path: str):
    """Show overall email metrics."""
    df = load_audit_data(csv_path)
    if df.empty:
        return

    metrics = calculate_overall_metrics(df)
    click.echo("=== 📊 EMAIL METRICS ===")
    click.echo(f"Total Emails: {int(metrics['total_emails'])}")
    click.echo(f"Unread Rate: {metrics['unread_percentage']:.1f}%")
    click.echo(f"Average Open Rate: {metrics['average_open_rate']:.1f}%")
    click.echo(f"Senders Never Opened: {int(metrics['senders_never_opened'])}")
    click.echo(f"Top Ignorance Score: {metrics['top_ignorance_score']:.0f}")


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
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
def progress(csv_path: str):
    """Show cleanup progress compared to baseline."""
    df = load_audit_data(csv_path)
    if df.empty:
        return

    current_metrics = calculate_overall_metrics(df)

    # Calculate improvements
    unread_improvement = BASELINE_METRICS["unread_percentage"] - current_metrics["unread_percentage"]
    top_score_reduction = BASELINE_METRICS["top_ignorance_score"] - current_metrics["top_ignorance_score"]
    top_score_reduction_pct = top_score_reduction / BASELINE_METRICS["top_ignorance_score"] * 100
    open_rate_improvement = current_metrics["average_open_rate"] - BASELINE_METRICS["average_open_rate"]

    click.echo("=== 📈 CLEANUP PROGRESS ===")
    click.echo(f"📉 Unread Rate Improvement: {unread_improvement:.1f}%")
    click.echo(f"🎯 Top Score Reduction: {top_score_reduction:.0f} ({top_score_reduction_pct:.0f}%)")
    click.echo(f"📈 Open Rate Improvement: {open_rate_improvement:.1f}%")


@cli.command()
@click.option("--cache-path", default="data/email_cache.json", help="Path to the email cache file")
@click.option("--top-n", default=3, help="Number of top senders to analyze")
def title_patterns(cache_path: str, top_n: int):
    """Analyze title patterns for top senders."""
    try:
        with open(cache_path, "r") as f:
            cache = json.load(f)
    except FileNotFoundError:
        click.echo(f"Error: {cache_path} not found. Run audit first.")
        return

    # Group by sender and collect subjects
    sender_subjects = defaultdict(list)
    for email in cache.values():
        headers = email.get("payload", {}).get("headers", [])
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender_subjects[sender].append(subject)

    # Get top senders by volume
    top_senders = sorted(sender_subjects.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]

    click.echo(f"=== 📧 TITLE PATTERNS FOR TOP {top_n} SENDERS ===")
    for sender, subjects in top_senders:
        click.echo(f"\n## {sender} ({len(subjects)} emails)")

        # Analyze common words in subjects
        words = []
        for subj in subjects:
            # Split subject and filter out short/common words
            subj_words = [
                word.lower()
                for word in subj.split()
                if len(word) > 3
                and word.lower()
                not in [
                    "with",
                    "from",
                    "your",
                    "this",
                    "that",
                    "have",
                    "been",
                    "will",
                    "they",
                    "their",
                    "there",
                    "here",
                    "when",
                    "where",
                    "what",
                    "which",
                    "then",
                    "than",
                    "into",
                    "onto",
                    "over",
                    "under",
                    "after",
                    "before",
                    "while",
                    "since",
                    "until",
                    "through",
                    "during",
                    "between",
                    "among",
                    "within",
                ]
            ]
            words.extend(subj_words)

        if words:
            word_counts = Counter(words).most_common(10)
            click.echo("Common words in subjects:")
            for word, count in word_counts:
                click.echo(f"  • {word}: {count}")
        else:
            click.echo("No significant words found in subjects")


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
@click.option("--cache-path", default="data/email_cache.json", help="Path to the email cache file")
@click.option("--top-n", default=5, help="Number of top problematic senders to analyze")
def problematic_titles(csv_path: str, cache_path: str, top_n: int):
    """Analyze title patterns for top problematic senders (by ignorance score)."""
    # Load CSV to get top noise makers
    df = load_audit_data(csv_path)
    if df.empty:
        click.echo(f"Error: {csv_path} not found. Run audit first.")
        return

    # Get top problematic senders by ignorance score
    top_problematic = get_top_noise_makers(df, top_n)
    problematic_senders = set(top_problematic["from"].tolist())

    # Load cache to analyze their email subjects
    try:
        with open(cache_path, "r") as f:
            cache = json.load(f)
    except FileNotFoundError:
        click.echo(f"Error: {cache_path} not found. Run audit first.")
        return

    # Group subjects by sender (only for problematic senders)
    sender_subjects = defaultdict(list)
    for email in cache.values():
        headers = email.get("payload", {}).get("headers", [])
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        if sender in problematic_senders:
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
            sender_subjects[sender].append(subject)

    click.echo(f"=== 🚨 TITLE PATTERNS FOR TOP {top_n} PROBLEMATIC SENDERS ===")
    click.echo("(Ranked by ignorance score - high volume + low engagement)")
    click.echo()

    for _, row in top_problematic.iterrows():
        sender = row["from"]
        subjects = sender_subjects.get(sender, [])

        if not subjects:
            click.echo(f"## {sender}")
            click.echo("No cached emails found for this sender")
            continue

        click.echo(f"## {sender} ({len(subjects)} emails, Score: {row['ignorance_score']:.0f})")

        # Analyze common words in subjects
        words = []
        for subj in subjects:
            # Split subject and filter out short/common words
            subj_words = [
                word.lower()
                for word in subj.split()
                if len(word) > 3
                and word.lower()
                not in [
                    "with",
                    "from",
                    "your",
                    "this",
                    "that",
                    "have",
                    "been",
                    "will",
                    "they",
                    "their",
                    "there",
                    "here",
                    "when",
                    "where",
                    "what",
                    "which",
                    "then",
                    "than",
                    "into",
                    "onto",
                    "over",
                    "under",
                    "after",
                    "before",
                    "while",
                    "since",
                    "until",
                    "through",
                    "during",
                    "between",
                    "among",
                    "within",
                ]
            ]
            words.extend(subj_words)

        if words:
            word_counts = Counter(words).most_common(10)
            click.echo("Common words in subjects:")
            for word, count in word_counts:
                click.echo(f"  • {word}: {count}")
        else:
            click.echo("No significant words found in subjects")

        click.echo()


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
def summary(csv_path: str):
    """Show email distribution summary and statistics."""
    df = load_audit_data(csv_path)
    if df.empty:
        return

    total_emails = df["total_volume"].sum()

    click.echo("=== 📊 EMAIL DISTRIBUTION SUMMARY ===")
    click.echo(f"Total Emails: {total_emails}")
    click.echo(f"Unique Senders: {len(df)}")
    click.echo()

    # Top 10 senders by volume
    top_10_volume = df.nlargest(10, "total_volume")["total_volume"].sum()
    click.echo(f"📈 Top 10 Senders by Volume: {top_10_volume} emails ({top_10_volume / total_emails * 100:.1f}%)")
    click.echo()

    # Top 10 senders by ignorance score
    top_10_noise = df.nlargest(10, "ignorance_score")["total_volume"].sum()
    click.echo(f"🎯 Top 10 Noise Makers by Ignorance Score: {top_10_noise} emails ({top_10_noise / total_emails * 100:.1f}%)")
    click.echo()

    # Senders with 0 open rate
    zero_open = df[df["open_rate"] == 0]["total_volume"].sum()
    zero_open_senders = len(df[df["open_rate"] == 0])
    click.echo(f"🚫 Zero Engagement Senders: {zero_open_senders} senders, {zero_open} emails ({zero_open / total_emails * 100:.1f}%)")
    click.echo()

    # High volume senders (>50 emails)
    high_volume = df[df["total_volume"] > 50]["total_volume"].sum()
    high_volume_senders = len(df[df["total_volume"] > 50])
    click.echo(f"📊 High Volume Senders (>50 emails): {high_volume_senders} senders, {high_volume} emails ({high_volume / total_emails * 100:.1f}%)")
    click.echo()

    # Category breakdown
    categories = ["updates_count", "promotions_count", "social_count", "important_count"]
    click.echo("📂 Category Distribution:")
    for cat in categories:
        total = df[cat].sum()
        if total > 0:
            click.echo(f"  • {cat.replace('_count', '').title()}: {total} emails ({total / total_emails * 100:.1f}%)")


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
def engagement(csv_path: str):
    """Analyze sender engagement patterns and tiers."""
    df = load_audit_data(csv_path)
    if df.empty:
        return

    total_emails = df["total_volume"].sum()

    click.echo("=== 🎯 ENGAGEMENT ANALYSIS ===")
    click.echo(f"Total Emails: {total_emails}")
    click.echo()

    # Define engagement tiers
    high_engagement = df[df["open_rate"] >= 80]
    medium_engagement = df[(df["open_rate"] >= 50) & (df["open_rate"] < 80)]
    low_engagement = df[(df["open_rate"] > 0) & (df["open_rate"] < 50)]
    zero_engagement = df[df["open_rate"] == 0]

    tiers = [
        ("High Engagement (80-100%)", high_engagement),
        ("Medium Engagement (50-79%)", medium_engagement),
        ("Low Engagement (1-49%)", low_engagement),
        ("Zero Engagement (0%)", zero_engagement),
    ]

    for tier_name, tier_df in tiers:
        if len(tier_df) > 0:
            tier_emails = tier_df["total_volume"].sum()
            tier_senders = len(tier_df)
            avg_open_rate = tier_df["open_rate"].mean()
            click.echo(f"🎯 {tier_name}:")
            click.echo(f"  • {tier_senders} senders, {tier_emails} emails ({tier_emails / total_emails * 100:.1f}%)")
            click.echo(f"  • Average open rate: {avg_open_rate:.1f}%")
            click.echo()

    # Show top performers in each tier
    if len(high_engagement) > 0:
        click.echo("🏆 Top High-Engagement Senders:")
        top_high = high_engagement.nlargest(3, "total_volume")
        for _, row in top_high.iterrows():
            click.echo(f"  • {row['from'][:40]:<40} | {int(row['total_volume']):3d} emails | {row['open_rate']:5.1f}% open")
        click.echo()


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
@click.option("--top-n", default=10, help="Number of top senders to show")
def top_volume(csv_path: str, top_n: int):
    """Show the top N senders by email volume."""
    df = load_audit_data(csv_path)
    if df.empty:
        return

    click.echo(f"=== 📈 TOP {top_n} SENDERS BY VOLUME ===")
    top_volume_senders = df.nlargest(top_n, "total_volume")[["from", "total_volume", "open_rate", "ignorance_score"]]

    for _, row in top_volume_senders.iterrows():
        click.echo(f"{row['from']:<50} | Vol: {int(row['total_volume']):3d} | Open: {row['open_rate']:5.1f}% | Score: {row['ignorance_score']:6.0f}")


if __name__ == "__main__":
    cli()
