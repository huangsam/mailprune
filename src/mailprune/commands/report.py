"""
Report command implementation for MailPrune.
"""

import click

from mailprune.utils import (
    BASELINE_METRICS,
    calculate_overall_metrics,
    calculate_percentage,
    get_category_distribution,
    get_engagement_tier_names,
    get_engagement_tiers,
    get_top_noise_makers,
    load_audit_data,
)


def generate_report(csv_path: str) -> None:
    """Generate a comprehensive email audit and cleanup report."""
    df = load_audit_data(csv_path)
    if df.empty:
        return

    current_metrics = calculate_overall_metrics(df)
    total_emails = df["total_volume"].sum()

    report = []
    report.append("=== 📧 COMPREHENSIVE EMAIL AUDIT REPORT ===")
    report.append("")

    # Current Status
    report.append("📊 CURRENT STATUS")
    report.append(f"   • {len(df)} unique senders")
    report.append(f"   • {int(current_metrics['total_emails'])} total emails")
    report.append(f"   • Unread Rate: {current_metrics['unread_percentage']:.1f}%")
    report.append(f"   • Average Open Rate: {current_metrics['average_open_rate']:.1f}%")
    report.append(f"   • Senders Never Opened: {int(current_metrics['senders_never_opened'])}")
    report.append(f"   • Top Ignorance Score: {current_metrics['top_ignorance_score']:.0f}")
    report.append("")

    # Progress Metrics
    if BASELINE_METRICS:
        unread_improvement = BASELINE_METRICS["unread_percentage"] - current_metrics["unread_percentage"]
        top_score_reduction = BASELINE_METRICS["top_ignorance_score"] - current_metrics["top_ignorance_score"]
        top_score_reduction_pct = top_score_reduction / BASELINE_METRICS["top_ignorance_score"] * 100
        open_rate_improvement = current_metrics["average_open_rate"] - BASELINE_METRICS["average_open_rate"]

        report.append("📈 IMPROVEMENT METRICS")
        report.append(f"   • Unread Rate Improvement: {unread_improvement:.1f}%")
        report.append(f"   • Top Score Reduction: {top_score_reduction:.0f} ({top_score_reduction_pct:.0f}%)")
        report.append(f"   • Open Rate Improvement: {open_rate_improvement:.1f}%")
        report.append("")

    # Distribution Summary
    top_10_volume = df.nlargest(10, "total_volume")["total_volume"].sum()
    top_10_noise = df.nlargest(10, "ignorance_score")["total_volume"].sum()
    zero_open = df[df["open_rate"] == 0]["total_volume"].sum()
    zero_open_senders = len(df[df["open_rate"] == 0])
    high_volume = df[df["total_volume"] > 50]["total_volume"].sum()
    high_volume_senders = len(df[df["total_volume"] > 50])

    report.append("📂 EMAIL DISTRIBUTION")
    report.append(f"   • Top 10 Senders by Volume: {top_10_volume} emails ({calculate_percentage(top_10_volume, total_emails)})")
    report.append(f"   • Top 10 Noise Makers: {top_10_noise} emails ({calculate_percentage(top_10_noise, total_emails)})")
    report.append(f"   • Zero Engagement: {zero_open_senders} senders, {zero_open} emails ({calculate_percentage(zero_open, total_emails)})")
    report.append(
        f"   • High Volume Senders (>50 emails): {high_volume_senders} senders, {high_volume} emails ({calculate_percentage(high_volume, total_emails)})"
    )
    report.append("")

    # Engagement Breakdown
    engagement_tiers = get_engagement_tiers(df)
    tier_names = get_engagement_tier_names()

    report.append("🎯 ENGAGEMENT BREAKDOWN")
    for tier_key, tier_df in engagement_tiers.items():
        if len(tier_df) > 0:
            tier_emails = tier_df["total_volume"].sum()
            report.append(f"   • {tier_names[tier_key]}: {len(tier_df)} senders, {tier_emails} emails ({calculate_percentage(tier_emails, total_emails)})")
    report.append("")

    # Category Distribution
    report.append("📂 EMAIL CATEGORIES")
    report.extend(get_category_distribution(df, total_emails))
    report.append("")

    # Top Noise Makers
    report.append("🏆 TOP 10 NOISE MAKERS")
    top10 = get_top_noise_makers(df, 10)
    for i, (_, row) in enumerate(top10.iterrows(), 1):
        report.append(f"{i:2d}. {row['from']:<50} | Vol: {int(row['total_volume']):3d} | Open: {row['open_rate']:5.1f}% | Score: {row['ignorance_score']:6.0f}")
    report.append("")

    # Cleanup Recommendations
    report.append("🎯 CLEANUP RECOMMENDATIONS")

    # Zero engagement senders
    never_opened = df[df.open_rate == 0].nlargest(5, "total_volume")
    if not never_opened.empty:
        report.append("🗑️  PRIORITY: Unsubscribe from these (0% open rate):")
        for _, row in never_opened.iterrows():
            report.append(f"      • {row['from']} ({int(row['total_volume'])} emails)")
        report.append("")

    # High volume, low engagement
    high_volume_noise = df[(df.total_volume >= 20) & (df.open_rate < 50)].nlargest(5, "ignorance_score")
    if not high_volume_noise.empty:
        report.append("🎛️  REVIEW: High-volume, low-engagement senders:")
        for _, row in high_volume_noise.iterrows():
            report.append(f"      • {row['from']} ({int(row['total_volume'])} emails, {row['open_rate']:.1f}% open)")
        report.append("")

    # Top high-engagement senders
    high_engagement = engagement_tiers["high"]
    if len(high_engagement) > 0:
        report.append("✅ KEEP: Your most engaged senders:")
        top_engaged = high_engagement.nlargest(3, "total_volume")
        for _, row in top_engaged.iterrows():
            report.append(f"      • {row['from'][:40]:<40} ({int(row['total_volume'])} emails, {row['open_rate']:.1f}% open)")

    click.echo("\n".join(report))
