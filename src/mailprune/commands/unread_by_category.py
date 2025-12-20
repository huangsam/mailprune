"""
Unread by category command implementation for MailPrune.
"""

import click

from mailprune import load_audit_data
from mailprune.utils import calculate_percentage


def analyze_unread_by_category(csv_path: str) -> None:
    """Analyze unread emails grouped by Gmail categories."""
    df = load_audit_data(csv_path)
    if df.empty:
        return

    total_unread = df["unread_count"].sum()
    total_emails = df["total_volume"].sum()

    click.echo("=== 📧 UNREAD EMAILS BY CATEGORY ===")
    click.echo(f"Total Unread Emails: {int(total_unread)} out of {int(total_emails)} ({calculate_percentage(total_unread, total_emails)})")
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
