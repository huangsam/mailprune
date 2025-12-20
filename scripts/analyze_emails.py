#!/usr/bin/env python3
"""
Email Analysis Script for mailprune.
Provides various analysis functions for email audit data.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import click

# Add the src directory to the path so we can import mailprune
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from mailprune import BASELINE_METRICS, analyze_sender_patterns, calculate_overall_metrics, generate_cleanup_report, get_top_noise_makers, load_audit_data


@click.group()
def cli():
    """Email analysis tools for mailprune audit data."""
    pass


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


if __name__ == "__main__":
    cli()
