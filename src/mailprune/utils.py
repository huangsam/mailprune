"""
Utility functions for the mailprune project.
"""

import json
import logging
import os
from typing import Any, Dict

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
