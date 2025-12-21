"""
Enhanced title patterns command with NLP processing for MailPrune.
"""

from typing import Dict, List

import click

from mailprune.utils.analysis import analyze_title_patterns_core


def analyze_title_patterns_enhanced(cache_path: str, audit_data: List[Dict], top_n: int = 5, by: str = "volume", use_nlp: bool = True) -> Dict:
    """Enhanced title pattern analysis with NLP."""
    results = analyze_title_patterns_core(cache_path, audit_data, top_n, by, use_nlp)

    # Display results
    click.echo(f"\nEnhanced Title Pattern Analysis (Top {top_n} Senders by {by})")
    click.echo("=" * 60)

    for sender, data in results.items():
        click.echo(f"\nSender: {sender}")
        click.echo(f"Sample Subject: {data['sample_subject']}")
        click.echo(f"NLP Used: {data['nlp_used']}")
        click.echo("Top Keywords:")
        for keyword, count in data["top_keywords"]:
            click.echo(f"  {keyword}: {count}")

    return results
