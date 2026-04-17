"""
Engagement command implementation for Mailprune.
"""

from mailprune.utils import (
    calculate_percentage,
    get_engagement_tier_names,
    get_engagement_tiers,
    load_audit_data,
)


def analyze_engagement(csv_path: str, tier: str) -> str:
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
        return "No audit data found. Run 'mailprune audit' first."

    total_emails = df["total_volume"].sum()

    output = []
    output.append("=== 🎯 ENGAGEMENT ANALYSIS ===")
    output.append(f"Total Emails: {total_emails}")
    output.append("")

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
                output.append(f"🎯 {tier_names[tier_key]}:")
                output.append(f"  • {tier_senders} senders, {tier_emails} emails ({calculate_percentage(tier_emails, total_emails)})")
                output.append(f"  • Average open rate: {avg_open_rate:.1f}%")
                output.append("")

        # Show top performers in high engagement tier
        high_engagement = engagement_tiers["high"]
        if len(high_engagement) > 0:
            output.append("🏆 Top High-Engagement Senders:")
            top_high = high_engagement.nlargest(3, "total_volume")
            for _, row in top_high.iterrows():
                output.append(f"  • {row['from'][:40]:<40} | {int(row['total_volume']):3d} emails | {row['open_rate']:5.1f}% open")
            output.append("")
    else:
        # Show detailed listing for specific tier
        if tier not in engagement_tiers:
            return f"Invalid tier: {tier}. Use 'high', 'medium', 'low', or 'zero'."

        tier_df = engagement_tiers[tier]
        if len(tier_df) == 0:
            return f"No senders found in {tier_names[tier].lower()}."

        tier_emails = tier_df["total_volume"].sum()
        output.append(f"=== 🚫 {tier_names[tier].upper()} SENDERS ===")
        output.append(f"Total: {len(tier_df)} senders, {tier_emails} emails ({calculate_percentage(tier_emails, total_emails)})")
        output.append("")

        # Sort by volume descending and show all senders in this tier
        sorted_senders = tier_df.sort_values("total_volume", ascending=False)
        for _, row in sorted_senders.iterrows():
            output.append(f"{int(row['total_volume']):2d} emails | {row['from']}")

    return "\n".join(output)
