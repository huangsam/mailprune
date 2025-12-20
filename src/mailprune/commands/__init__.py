"""
MailPrune CLI Commands

This package contains the implementation logic for CLI commands.
Each command is in its own module for better organization and maintainability.
"""

from .audit import perform_audit
from .engagement import analyze_engagement
from .report import generate_report
from .summary import show_summary
from .title_patterns import analyze_title_patterns
from .unread_by_category import analyze_unread_by_category

__all__ = [
    "analyze_engagement",
    "analyze_title_patterns",
    "analyze_unread_by_category",
    "generate_report",
    "perform_audit",
    "show_summary",
]
