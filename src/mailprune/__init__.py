# Mailprune package

from .utils import (
    BASELINE_METRICS,
    analyze_sender_email_patterns,
    analyze_sender_patterns,
    calculate_overall_metrics,
    compare_metrics,
    generate_cleanup_report,
    get_top_noise_makers,
    load_audit_data,
    perform_audit,
)

__all__ = [
    "BASELINE_METRICS",
    "analyze_sender_email_patterns",
    "analyze_sender_patterns",
    "calculate_overall_metrics",
    "compare_metrics",
    "generate_cleanup_report",
    "get_top_noise_makers",
    "load_audit_data",
    "perform_audit",
]

__version__ = "0.1.0"
