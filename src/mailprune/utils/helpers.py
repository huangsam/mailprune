"""
Utility functions for the mailprune project.
"""

import json
import logging
import os
from collections import defaultdict
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


def load_email_cache() -> Dict[str, Dict[str, Any]]:
    """Load cached email data from file."""
    cache_file = "data/email_cache.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache: {e}. Starting fresh.")
    return {}


def save_email_cache(cache: Dict[str, Dict[str, Any]]) -> None:
    """Save email data to cache file."""
    cache_file = "data/email_cache.json"
    try:
        with open(cache_file, "w") as f:
            json.dump(cache, f, indent=2)
        logger.info(f"Saved {len(cache)} emails to cache")
    except IOError as e:
        logger.error(f"Failed to save cache: {e}")


# Common constants
EMAIL_CATEGORIES = ["updates_count", "promotions_count", "social_count", "important_count"]


def get_engagement_tier_names() -> Dict[str, str]:
    """Get human-readable engagement tier names."""
    return {
        "high": "High Engagement (80-100%)",
        "medium": "Medium Engagement (50-79%)",
        "low": "Low Engagement (1-49%)",
        "zero": "Zero Engagement (0%)",
    }


def calculate_percentage(value: float, total: float) -> str:
    """Calculate percentage and format as string."""
    if total == 0:
        return "0.0%"
    return f"{value / total * 100:.1f}%"


def format_sender_list(df: pd.DataFrame, max_name_length: int = 40) -> List[str]:
    """Format a dataframe of senders for display."""
    return [
        f"{row['from'][:max_name_length]:<{max_name_length}} | {int(row['total_volume']):3d} emails | {row['open_rate']:5.1f}% open" for _, row in df.iterrows()
    ]


def get_sender_subjects_from_cache(cache: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract sender-subject mapping from email cache."""
    sender_subjects = defaultdict(list)
    for email in cache.values():
        headers = email.get("payload", {}).get("headers", [])
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender_subjects[sender].append(subject)
    return dict(sender_subjects)


def filter_common_words(words: List[str]) -> List[str]:
    """Filter out common English words and short words from subject analysis.

    Removes common prepositions, articles, and conjunctions that don't provide
    meaningful insight into email patterns. Also filters out words shorter
    than 4 characters to focus on more significant terms.

    Args:
        words: List of words extracted from email subjects

    Returns:
        Filtered list of words suitable for pattern analysis
    """
    common_words = {
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
    }
    return [word.lower() for word in words if len(word) > 3 and word.lower() not in common_words]


def get_category_distribution(df: pd.DataFrame, total_emails: int) -> List[str]:
    """Get formatted category distribution lines."""
    lines = []
    for cat in EMAIL_CATEGORIES:
        total = df[cat].sum()
        if total > 0:
            lines.append(f"  • {cat.replace('_count', '').title()}: {total} emails ({calculate_percentage(total, total_emails)})")
    return lines
