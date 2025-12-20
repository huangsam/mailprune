# Mailprune package

from .constants import (
    DEFAULT_CACHE_PATH,
    DEFAULT_CREDENTIALS_PATH,
    DEFAULT_CSV_PATH,
    DEFAULT_MAX_EMAILS,
    DEFAULT_POOL_SIZE,
    DEFAULT_TOKEN_PATH,
    ENGAGEMENT_HIGH_THRESHOLD,
    ENGAGEMENT_LOW_THRESHOLD,
    ENGAGEMENT_MEDIUM_THRESHOLD,
    GMAIL_API_SCOPES,
    GMAIL_API_SERVICE_NAME,
    GMAIL_API_VERSION,
    GmailLabels,
)
from .utils import (
    BASELINE_METRICS,
    analyze_sender_email_patterns,
    analyze_sender_patterns,
    calculate_overall_metrics,
    cluster_senders_unsupervised,
    compare_metrics,
    generate_cleanup_report,
    get_top_noise_makers,
    load_audit_data,
)

__all__ = [
    # Constants
    "DEFAULT_CACHE_PATH",
    "DEFAULT_CREDENTIALS_PATH",
    "DEFAULT_CSV_PATH",
    "DEFAULT_MAX_EMAILS",
    "DEFAULT_POOL_SIZE",
    "DEFAULT_TOKEN_PATH",
    "ENGAGEMENT_HIGH_THRESHOLD",
    "ENGAGEMENT_LOW_THRESHOLD",
    "ENGAGEMENT_MEDIUM_THRESHOLD",
    "GMAIL_API_SCOPES",
    "GMAIL_API_SERVICE_NAME",
    "GMAIL_API_VERSION",
    "GmailLabels",
    # Functions
    "BASELINE_METRICS",
    "analyze_sender_email_patterns",
    "analyze_sender_patterns",
    "calculate_overall_metrics",
    "cluster_senders_unsupervised",
    "compare_metrics",
    "generate_cleanup_report",
    "get_top_noise_makers",
    "load_audit_data",
]

__version__ = "0.1.0"
