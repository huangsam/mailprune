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
@click.option("--cache-path", default="data/email_cache.json", help="Path to the email cache file")
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file (required for ignorance ranking)")
@click.option("--top-n", default=5, help="Number of top senders to analyze")
@click.option("--by", default="volume", type=click.Choice(["volume", "ignorance"]), help="Rank senders by volume or ignorance score")
def title_patterns(cache_path: str, csv_path: str, top_n: int, by: str):
    """Analyze title patterns for top senders (by volume or ignorance score)."""
    # Load cache
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

    # Select top senders based on ranking method
    if by == "ignorance":
        # Load CSV for ignorance score ranking
        df = load_audit_data(csv_path)
        if df.empty:
            click.echo(f"Error: {csv_path} not found. Run audit first.")
            return

        # Get top problematic senders by ignorance score
        top_senders_data = get_top_noise_makers(df, top_n)
        selected_senders = [(row["from"], row["ignorance_score"]) for _, row in top_senders_data.iterrows()]
        title = f"=== 🚨 TITLE PATTERNS FOR TOP {top_n} PROBLEMATIC SENDERS ==="
        subtitle = "(Ranked by ignorance score - high volume + low engagement)"
    else:  # by == "volume"
        # Get top senders by volume
        top_senders = sorted(sender_subjects.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]
        selected_senders = [(sender, len(subjects)) for sender, subjects in top_senders]
        title = f"=== 📧 TITLE PATTERNS FOR TOP {top_n} SENDERS ==="
        subtitle = "(Ranked by email volume)"

    click.echo(title)
    if by == "ignorance":
        click.echo(subtitle)
    click.echo()

    for sender, score_or_count in selected_senders:
        subjects = sender_subjects.get(sender, [])

        if not subjects:
            click.echo(f"## {sender}")
            click.echo("No cached emails found for this sender")
            continue

        if by == "ignorance":
            click.echo(f"## {sender} ({len(subjects)} emails, Score: {score_or_count:.0f})")
        else:
            click.echo(f"## {sender} ({score_or_count} emails)")

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
@click.option("--tier", type=click.Choice(["high", "medium", "low", "zero", "all"]), default="all", help="Show detailed listing for specific engagement tier")
def engagement(csv_path: str, tier: str):
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


@cli.command()
@click.option("--csv-path", default="data/noise_report.csv", help="Path to the audit CSV file")
def unread_by_category(csv_path: str):
    """Analyze unread emails grouped by Gmail categories."""
    df = load_audit_data(csv_path)
    if df.empty:
        return

    total_unread = df["unread_count"].sum()
    total_emails = df["total_volume"].sum()

    click.echo("=== 📧 UNREAD EMAILS BY CATEGORY ===")
    click.echo(f"Total Unread Emails: {int(total_unread)} out of {int(total_emails)} ({total_unread / total_emails * 100:.1f}%)")
    click.echo()

    # Categories to analyze
    categories = {"Updates": "updates_count", "Promotions": "promotions_count", "Social": "social_count", "Important": "important_count"}

    unread_by_category = {}
    total_by_category = {}

    # Calculate unread emails per category proportionally
    for cat_name, cat_col in categories.items():
        # Total emails in this category across all senders
        total_by_category[cat_name] = df[cat_col].sum()

        # Distribute unread emails proportionally per sender
        unread_in_cat = 0
        for _, row in df.iterrows():
            sender_total = row["total_volume"]
            sender_unread = row["unread_count"]
            sender_cat_count = row[cat_col]

            if sender_total > 0 and sender_cat_count > 0:
                # Proportional unread in this category for this sender
                proportion = sender_cat_count / sender_total
                unread_in_cat += sender_unread * proportion

        unread_by_category[cat_name] = int(unread_in_cat)

    # Display results
    click.echo("📂 Unread Emails by Category:")
    for cat_name in categories.keys():
        unread_count = unread_by_category[cat_name]
        total_count = total_by_category[cat_name]
        if total_count > 0:
            unread_pct = unread_count / total_count * 100
            click.echo(f"  • {cat_name}: {unread_count} unread out of {int(total_count)} ({unread_pct:.1f}%)")
    click.echo()

    # Recommendations based on unread patterns
    click.echo("🎯 CLEANUP RECOMMENDATIONS FOR UNREAD EMAILS:")
    click.echo()

    if unread_by_category.get("Promotions", 0) > 0:
        unread_promo = unread_by_category["Promotions"]
        click.echo(f"🛒 PROMOTIONS ({unread_promo} unread):")
        click.echo("  • Review for legitimate purchases/receipts vs marketing")
        click.echo("  • Unsubscribe from promotional newsletters")
        click.echo("  • Archive old promotional content")
        click.echo()

    if unread_by_category.get("Updates", 0) > 0:
        unread_updates = unread_by_category["Updates"]
        click.echo(f"📬 UPDATES ({unread_updates} unread):")
        click.echo("  • Check for important notifications (GitHub, banking, subscriptions)")
        click.echo("  • Unsubscribe from low-value update emails")
        click.echo("  • Mark informational updates as read")
        click.echo()

    if unread_by_category.get("Social", 0) > 0:
        unread_social = unread_by_category["Social"]
        click.echo(f"👥 SOCIAL ({unread_social} unread):")
        click.echo("  • Review social media notifications")
        click.echo("  • Adjust notification settings for social platforms")
        click.echo()

    if unread_by_category.get("Important", 0) > 0:
        unread_important = unread_by_category["Important"]
        click.echo(f"⭐ IMPORTANT ({unread_important} unread):")
        click.echo("  • Prioritize reviewing these - Gmail marked them as important")
        click.echo("  • Address time-sensitive items first")
        click.echo()

    # Show top unread senders by category
    click.echo("🏆 TOP UNREAD SENDERS BY CATEGORY:")
    for cat_name, cat_col in categories.items():
        if unread_by_category[cat_name] > 0:
            # Find senders with highest unread in this category (proportional)
            df[f"{cat_col}_unread"] = df.apply(lambda row: row["unread_count"] * (row[cat_col] / row["total_volume"]) if row["total_volume"] > 0 else 0, axis=1)
            top_unread_cat = df.nlargest(3, f"{cat_col}_unread")
            if not top_unread_cat.empty:
                click.echo(f"\n{cat_name.upper()}:")
                for _, row in top_unread_cat.iterrows():
                    unread_cat = int(row[f"{cat_col}_unread"])
                    if unread_cat > 0:
                        click.echo(f"  • {row['from']} | {unread_cat} unread")


if __name__ == "__main__":
    cli()
