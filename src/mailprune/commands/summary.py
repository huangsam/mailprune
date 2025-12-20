"""
Summary command implementation for MailPrune.
"""

import click

from mailprune import load_audit_data
from mailprune.utils import calculate_percentage, get_category_distribution


def show_summary(csv_path: str) -> None:
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
    click.echo(f"📈 Top 10 Senders by Volume: {top_10_volume} emails ({calculate_percentage(top_10_volume, total_emails)})")
    click.echo()

    # Top 10 senders by ignorance score
    top_10_noise = df.nlargest(10, "ignorance_score")["total_volume"].sum()
    click.echo(f"🎯 Top 10 Noise Makers by Ignorance Score: {top_10_noise} emails ({calculate_percentage(top_10_noise, total_emails)})")
    click.echo()

    # Senders with 0 open rate
    zero_open = df[df["open_rate"] == 0]["total_volume"].sum()
    zero_open_senders = len(df[df["open_rate"] == 0])
    click.echo(f"🚫 Zero Engagement Senders: {zero_open_senders} senders, {zero_open} emails ({calculate_percentage(zero_open, total_emails)})")
    click.echo()

    # High volume senders (>50 emails)
    high_volume = df[df["total_volume"] > 50]["total_volume"].sum()
    high_volume_senders = len(df[df["total_volume"] > 50])
    click.echo(f"📊 High Volume Senders (>50 emails): {high_volume_senders} senders, {high_volume} emails ({calculate_percentage(high_volume, total_emails)})")
    click.echo()

    # Category breakdown
    click.echo("📂 Category Distribution:")
    category_lines = get_category_distribution(df, total_emails)
    for line in category_lines:
        click.echo(line)
