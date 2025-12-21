"""
Content patterns command with NLP processing for MailPrune.
Analyzes email content snippets for comprehensive pattern recognition.
"""

from typing import Dict, List

import click

from mailprune.utils.analysis import analyze_title_patterns_core


def analyze_patterns(cache_path: str, audit_data: List[Dict], top_n: int = 5, by: str = "volume", use_nlp: bool = True) -> Dict:
    """Analyze content patterns for top senders using email snippets."""
    results = analyze_title_patterns_core(cache_path, audit_data, top_n, by, use_nlp)

    # Display results
    click.echo(f"\nContent Pattern Analysis (Top {top_n} Senders by {by})")
    click.echo("=" * 60)

    for sender, data in results.items():
        click.echo(f"\nSender: {sender}")
        click.echo(f"Sample Subject: {data['sample_subject']}")
        click.echo(f"Emails Analyzed: {data['email_count']}")
        click.echo(f"NLP Processing: {'Enabled' if data['nlp_used'] else 'Disabled'}")

        click.echo("Top Keywords from Email Content:")
        keyword_strs = [f"{keyword} ({count})" for keyword, count in data["top_keywords"]]
        click.echo(f"  {', '.join(keyword_strs)}")

        # Display entities if available
        if "top_entities" in data and data["top_entities"]:
            click.echo("Extracted Entities:")
            for label, entities in data["top_entities"].items():
                if entities:
                    entity_strs = [f"{entity} ({count})" for entity, count in entities]
                    click.echo(f"  {label}: {', '.join(entity_strs)}")

    return results
