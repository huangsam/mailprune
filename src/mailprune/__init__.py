# Mailprune package

from .analysis import (
    load_audit_data,
    get_top_noise_makers,
    calculate_overall_metrics,
    analyze_sender_patterns,
    generate_cleanup_report,
    BASELINE_METRICS
)

__version__ = "0.1.0"
