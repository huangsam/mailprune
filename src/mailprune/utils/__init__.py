"""
MailPrune utility modules.

This package contains utility functions organized by domain:
- analysis.py: Email analysis and metrics functions
- audit.py: Gmail API integration and audit functions
- helpers.py: General utility and helper functions
"""

from .analysis import (
    BASELINE_METRICS,
    analyze_sender_email_patterns,
    analyze_sender_patterns,
    calculate_overall_metrics,
    compare_metrics,
    filter_common_words,
    generate_cleanup_report,
    get_engagement_tiers,
    get_top_noise_makers,
    get_top_senders_by_volume,
    load_audit_data,
)
from .audit import (
    get_sender_subjects_from_cache,
)
from .helpers import (
    EMAIL_CATEGORIES,
    calculate_percentage,
    format_sender_list,
    get_category_distribution,
    get_engagement_tier_names,
    load_email_cache,
    save_email_cache,
)

__all__ = [
    # From analysis
    "BASELINE_METRICS",
    "analyze_sender_email_patterns",
    "analyze_sender_patterns",
    "calculate_overall_metrics",
    "compare_metrics",
    "filter_common_words",
    "generate_cleanup_report",
    "get_engagement_tiers",
    "get_top_noise_makers",
    "get_top_senders_by_volume",
    "load_audit_data",
    # From audit
    "get_sender_subjects_from_cache",
    # From helpers
    "EMAIL_CATEGORIES",
    "calculate_percentage",
    "format_sender_list",
    "get_category_distribution",
    "get_engagement_tier_names",
    "load_email_cache",
    "save_email_cache",
]
