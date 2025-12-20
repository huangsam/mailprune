"""
Title patterns command implementation for MailPrune.
"""

import json
from collections import Counter, defaultdict

import click

from mailprune import get_top_noise_makers, load_audit_data


def analyze_title_patterns(cache_path: str, csv_path: str, top_n: int, by: str) -> None:
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
