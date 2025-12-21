"""
Utility functions for the mailprune project.
"""

import json
import logging
import os
from typing import Any, Callable, Dict, Generic, List, TypeVar

import pandas as pd

from ..constants import DEFAULT_CACHE_PATH

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ChainableFallback(Generic[T]):
    """A chainable fallback system that tries multiple strategies in order.

    Each strategy is a callable that may raise an exception. If a strategy
    succeeds (doesn't raise), its result is returned. If it fails, the next
    strategy is tried. If all strategies fail, a default fallback is used.
    """

    def __init__(self, default_fallback: Callable[[], T]) -> None:
        """Initialize with a default fallback strategy.

        Args:
            default_fallback: Callable that returns the default result if all strategies fail
        """
        self.strategies: List[Callable[[], T]] = []
        self.default_fallback = default_fallback

    def then(self, strategy: Callable[[], T]) -> "ChainableFallback[T]":
        """Add another strategy to the chain.

        Args:
            strategy: A callable that may raise an exception

        Returns:
            Self for method chaining
        """
        self.strategies.append(strategy)
        return self

    def execute(self) -> T:
        """Execute the chain of strategies.

        Returns:
            Result from the first successful strategy, or default fallback
        """
        for strategy in self.strategies:
            try:
                return strategy()
            except Exception:
                continue

        # All strategies failed, use default
        return self.default_fallback()


def load_email_cache(cache_path: str = DEFAULT_CACHE_PATH) -> Dict[str, Dict[str, Any]]:
    """Load cached email data from file."""
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache: {e}. Starting fresh.")
    return {}


def save_email_cache(cache: Dict[str, Dict[str, Any]], cache_path: str = DEFAULT_CACHE_PATH) -> None:
    """Save email data to cache file."""
    try:
        with open(cache_path, "w") as f:
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


def get_category_distribution(df: pd.DataFrame, total_emails: int) -> List[str]:
    """Get formatted category distribution lines."""
    lines = []
    for cat in EMAIL_CATEGORIES:
        total = df[cat].sum()
        if total > 0:
            lines.append(f"  • {cat.replace('_count', '').title()}: {total} emails ({calculate_percentage(total, total_emails)})")
    return lines
