"""
Engagement command implementation for MailPrune.
"""

import click

from mailprune import load_audit_data


def analyze_engagement(csv_path: str, tier: str) -> None:
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

    # Show overview for all tiers or just the selected tier
    if tier == "all":
        for tier_name, tier_df in tiers:
            if len(tier_df) > 0:
                tier_emails = tier_df["total_volume"].sum()
                tier_senders = len(tier_df)
                avg_open_rate = tier_df["open_rate"].mean()
                click.echo(f"🎯 {tier_name}:")
                click.echo(f"  • {tier_senders} senders, {tier_emails} emails ({tier_emails / total_emails * 100:.1f}%)")
                click.echo(f"  • Average open rate: {avg_open_rate:.1f}%")
                click.echo()

        # Show top performers in high engagement tier
        if len(high_engagement) > 0:
            click.echo("🏆 Top High-Engagement Senders:")
            top_high = high_engagement.nlargest(3, "total_volume")
            for _, row in top_high.iterrows():
                click.echo(f"  • {row['from'][:40]:<40} | {int(row['total_volume']):3d} emails | {row['open_rate']:5.1f}% open")
            click.echo()
    else:
        # Show detailed listing for specific tier
        tier_map = {
            "high": ("High Engagement (80-100%)", high_engagement),
            "medium": ("Medium Engagement (50-79%)", medium_engagement),
            "low": ("Low Engagement (1-49%)", low_engagement),
            "zero": ("Zero Engagement (0%)", zero_engagement),
        }

        tier_name, tier_df = tier_map[tier]
        if len(tier_df) == 0:
            click.echo(f"No senders found in {tier_name.lower()}.")
            return

        tier_emails = tier_df["total_volume"].sum()
        click.echo(f"=== 🚫 {tier_name.upper()} SENDERS ===")
        click.echo(f"Total: {len(tier_df)} senders, {tier_emails} emails ({tier_emails / total_emails * 100:.1f}%)")
        click.echo()

        # Sort by volume descending and show all senders in this tier
        sorted_senders = tier_df.sort_values("total_volume", ascending=False)
        for _, row in sorted_senders.iterrows():
            click.echo(f"{int(row['total_volume']):2d} emails | {row['from']}")
