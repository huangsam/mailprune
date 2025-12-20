"""
Title patterns command implementation for MailPrune.
"""

from collections import Counter

import click

from mailprune.utils import (
    filter_common_words,
    get_sender_subjects_from_cache,
    get_top_noise_makers,
    get_top_senders_by_volume,
    load_audit_data,
    load_email_cache,
)


def analyze_title_patterns(cache_path: str, csv_path: str, top_n: int, by: str) -> None:
    """Analyze title patterns for top senders (by volume or ignorance score)."""
    # Load cache
    cache = load_email_cache()
    if not cache:
        click.echo(f"Error: {cache_path} not found. Run audit first.")
        return

    # Group by sender and collect subjects
    sender_subjects = get_sender_subjects_from_cache(cache)

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
        selected_senders = get_top_senders_by_volume(sender_subjects, top_n)
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
            subj_words = subj.split()
            filtered_words = filter_common_words(subj_words)
            words.extend(filtered_words)

        if words:
            word_counts = Counter(words).most_common(10)
            click.echo("Common words in subjects:")
            for word, count in word_counts:
                click.echo(f"  • {word}: {count}")
        else:
            click.echo("No significant words found in subjects")

        click.echo()
