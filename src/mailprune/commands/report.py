"""
Report command implementation for MailPrune.
"""

import click

from mailprune import BASELINE_METRICS, calculate_overall_metrics, get_top_noise_makers, load_audit_data


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
    report.append(f"   • Top 10 Senders by Volume: {top_10_volume} emails ({top_10_volume / total_emails * 100:.1f}%)")
    report.append(f"   • Top 10 Noise Makers: {top_10_noise} emails ({top_10_noise / total_emails * 100:.1f}%)")
    report.append(f"   • Zero Engagement: {zero_open_senders} senders, {zero_open} emails ({zero_open / total_emails * 100:.1f}%)")
    report.append(f"   • High Volume Senders (>50 emails): {high_volume_senders} senders, {high_volume} emails ({high_volume / total_emails * 100:.1f}%)")
    report.append("")

    # Engagement Breakdown
    high_engagement = df[df["open_rate"] >= 80]
    medium_engagement = df[(df["open_rate"] >= 50) & (df["open_rate"] < 80)]
    low_engagement = df[(df["open_rate"] > 0) & (df["open_rate"] < 50)]
    zero_engagement = df[df["open_rate"] == 0]

    report.append("🎯 ENGAGEMENT BREAKDOWN")
    if len(high_engagement) > 0:
        tier_emails = high_engagement["total_volume"].sum()
        report.append(f"   • High Engagement (80-100%): {len(high_engagement)} senders, {tier_emails} emails ({tier_emails / total_emails * 100:.1f}%)")
    if len(medium_engagement) > 0:
        tier_emails = medium_engagement["total_volume"].sum()
        report.append(f"   • Medium Engagement (50-79%): {len(medium_engagement)} senders, {tier_emails} emails ({tier_emails / total_emails * 100:.1f}%)")
    if len(low_engagement) > 0:
        tier_emails = low_engagement["total_volume"].sum()
        report.append(f"   • Low Engagement (1-49%): {len(low_engagement)} senders, {tier_emails} emails ({tier_emails / total_emails * 100:.1f}%)")
    if len(zero_engagement) > 0:
        tier_emails = zero_engagement["total_volume"].sum()
        report.append(f"   • Zero Engagement (0%): {len(zero_engagement)} senders, {tier_emails} emails ({tier_emails / total_emails * 100:.1f}%)")
    report.append("")

    # Category Distribution
    categories = ["updates_count", "promotions_count", "social_count", "important_count"]
    report.append("📂 EMAIL CATEGORIES")
    for cat in categories:
        total = df[cat].sum()
        if total > 0:
            report.append(f"   • {cat.replace('_count', '').title()}: {total} emails ({total / total_emails * 100:.1f}%)")
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
    if len(high_engagement) > 0:
        report.append("✅ KEEP: Your most engaged senders:")
        top_engaged = high_engagement.nlargest(3, "total_volume")
        for _, row in top_engaged.iterrows():
            report.append(f"      • {row['from'][:40]:<40} ({int(row['total_volume'])} emails, {row['open_rate']:.1f}% open)")

    click.echo("\n".join(report))
