"""
Enhanced title patterns command with NLP processing for MailPrune.
"""

from typing import Dict, List

import click

from mailprune.constants import DEFAULT_CACHE_PATH, DEFAULT_CSV_PATH
from mailprune.utils.analysis import analyze_title_patterns_core, load_audit_data


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


@click.command()
@click.option("--top-n", default=5, help="Number of top senders to analyze")
@click.option("--no-nlp", is_flag=True, help="Disable NLP processing (use simple extraction)")
def title_patterns(top_n, no_nlp):
    """Enhanced title pattern analysis with NLP processing."""
    use_nlp = not no_nlp

    if not DEFAULT_CSV_PATH.exists():
        click.echo("No audit data found. Run 'mailprune audit' first.")
        return

    audit_data = load_audit_data(DEFAULT_CSV_PATH)

    if not audit_data:
        click.echo("No audit data available.")
        return

    results = analyze_title_patterns_enhanced(DEFAULT_CACHE_PATH, audit_data.to_dict("records"), top_n, "volume", use_nlp)

    if not results:
        click.echo("No title pattern data available.")
        return

    click.echo(f"\nEnhanced Title Pattern Analysis (Top {top_n} Senders)")
    click.echo("=" * 60)

    for sender, data in results.items():
        click.echo(f"\nSender: {sender}")
        click.echo(f"Sample Subject: {data['sample_subject']}")
        click.echo(f"NLP Processing: {'Enabled' if data['nlp_used'] else 'Disabled (fallback)'}")
        click.echo("Top Keywords:")

        for keyword, count in data["top_keywords"]:
            click.echo(f"  - {keyword}: {count}")

    click.echo("\nNote: Install NLP libraries with 'uv sync --group nlp' for enhanced processing.")
