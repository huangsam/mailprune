"""
Engagement command implementation for Mailprune.
"""

import click

from mailprune.utils import (
    calculate_percentage,
    get_engagement_tier_names,
    get_engagement_tiers,
    load_audit_data,
)


def analyze_engagement(csv_path: str, tier: str) -> None:
    """Analyze sender engagement patterns and tiers.

    This command categorizes email senders into engagement tiers based on their
    open rates and interaction patterns. It provides insights into how engaged
    you are with different senders and helps identify opportunities for cleanup.

    Engagement tiers include:
    - High: Frequently opened senders
    - Medium: Moderately engaged senders
    - Low: Rarely opened senders
    - Zero: Never opened senders

    The analysis shows statistics for each tier and highlights top performers
    in the high engagement category.
    """
    df = load_audit_data(csv_path)
    if df.empty:
        return

    total_emails = df["total_volume"].sum()

    click.echo("=== 🎯 ENGAGEMENT ANALYSIS ===")
    click.echo(f"Total Emails: {total_emails}")
    click.echo()

    # Define engagement tiers
    engagement_tiers = get_engagement_tiers(df)
    tier_names = get_engagement_tier_names()

    tiers = [
        ("high", engagement_tiers["high"]),
        ("medium", engagement_tiers["medium"]),
        ("low", engagement_tiers["low"]),
        ("zero", engagement_tiers["zero"]),
    ]

    # Show overview for all tiers or just the selected tier
    if tier == "all":
        for tier_key, tier_df in tiers:
            if len(tier_df) > 0:
                tier_emails = tier_df["total_volume"].sum()
                tier_senders = len(tier_df)
                avg_open_rate = tier_df["open_rate"].mean()
                click.echo(f"🎯 {tier_names[tier_key]}:")
                click.echo(f"  • {tier_senders} senders, {tier_emails} emails ({calculate_percentage(tier_emails, total_emails)})")
                click.echo(f"  • Average open rate: {avg_open_rate:.1f}%")
                click.echo()

        # Show top performers in high engagement tier
        high_engagement = engagement_tiers["high"]
        if len(high_engagement) > 0:
            click.echo("🏆 Top High-Engagement Senders:")
            top_high = high_engagement.nlargest(3, "total_volume")
            for _, row in top_high.iterrows():
                click.echo(f"  • {row['from'][:40]:<40} | {int(row['total_volume']):3d} emails | {row['open_rate']:5.1f}% open")
            click.echo()
    else:
        # Show detailed listing for specific tier
        if tier not in engagement_tiers:
            click.echo(f"Invalid tier: {tier}. Use 'high', 'medium', 'low', or 'zero'.")
            return

        tier_df = engagement_tiers[tier]
        if len(tier_df) == 0:
            click.echo(f"No senders found in {tier_names[tier].lower()}.")
            return

        tier_emails = tier_df["total_volume"].sum()
        click.echo(f"=== 🚫 {tier_names[tier].upper()} SENDERS ===")
        click.echo(f"Total: {len(tier_df)} senders, {tier_emails} emails ({calculate_percentage(tier_emails, total_emails)})")
        click.echo()

        # Sort by volume descending and show all senders in this tier
        sorted_senders = tier_df.sort_values("total_volume", ascending=False)
        for _, row in sorted_senders.iterrows():
            click.echo(f"{int(row['total_volume']):2d} emails | {row['from']}")
