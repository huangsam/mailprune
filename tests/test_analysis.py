"""
Tests for mailprune analysis functions.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import mailprune
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from mailprune import (  # noqa: E402
    BASELINE_METRICS,
    analyze_sender_email_patterns,
    analyze_sender_patterns,
    calculate_overall_metrics,
    compare_metrics,
    generate_cleanup_report,
    get_top_noise_makers,
    load_audit_data,
)


@pytest.fixture
def sample_audit_data():
    """Create sample audit data for testing."""
    return pd.DataFrame(
        {
            "from": ["test@example.com", "newsletter@company.com", "bank@bank.com", "promo@store.com", "important@service.com"],
            "total_volume": [10, 25, 5, 15, 8],
            "open_rate": [50.0, 10.0, 80.0, 0.0, 60.0],
            "ignorance_score": [500, 2250, 100, 1500, 320],
            "unread_count": [5, 22, 1, 15, 3],
        }
    )


class TestAnalysisFunctions:
    """Test the core analysis functions."""

    def test_calculate_overall_metrics(self, sample_audit_data):
        """Test calculation of overall email metrics."""
        metrics = calculate_overall_metrics(sample_audit_data)

        assert metrics["total_emails"] == 63  # sum of total_volume
        assert metrics["unread_percentage"] == pytest.approx(73.02, rel=1e-2)  # (46/63)*100
        assert metrics["average_open_rate"] == pytest.approx(40.0, rel=1e-2)  # mean of open_rate
        assert metrics["senders_never_opened"] == 1  # promo@store.com has 0% open rate
        assert metrics["top_ignorance_score"] == 2250  # newsletter@company.com

    def test_get_top_noise_makers(self, sample_audit_data):
        """Test getting top noise makers."""
        top_3 = get_top_noise_makers(sample_audit_data, 3)

        assert len(top_3) == 3
        assert top_3.iloc[0]["ignorance_score"] == 2250  # highest score
        assert top_3.iloc[1]["ignorance_score"] == 1500
        assert top_3.iloc[2]["ignorance_score"] == 500

    def test_analyze_sender_patterns_found(self, sample_audit_data):
        """Test analyzing a sender that exists."""
        result = analyze_sender_patterns(sample_audit_data, "newsletter")

        assert result is not None
        assert result["sender"] == "newsletter@company.com"
        assert result["total_emails"] == 25
        assert result["open_rate"] == 10.0
        assert result["ignorance_score"] == 2250
        assert result["unread_count"] == 22

    def test_analyze_sender_patterns_not_found(self, sample_audit_data):
        """Test analyzing a sender that doesn't exist."""
        result = analyze_sender_patterns(sample_audit_data, "nonexistent")

        assert result is None

    def test_compare_metrics(self):
        """Test comparing before and after metrics."""
        before = {"unread_percentage": 80.0, "top_ignorance_score": 3000, "average_open_rate": 10.0}
        after = {"unread_percentage": 70.0, "top_ignorance_score": 2000, "average_open_rate": 15.0}

        comparison = compare_metrics(before, after)

        assert comparison["unread_improvement"] == 10.0
        assert comparison["top_score_reduction"] == 1000
        assert comparison["top_score_reduction_pct"] == pytest.approx(33.33, rel=1e-2)
        assert comparison["open_rate_improvement"] == 5.0

    def test_analyze_sender_email_patterns(self):
        """Test analyzing email subject patterns."""
        subjects = [
            "Your credit score has changed",
            "Special loan offer - 0% APR",
            "Account balance update",
            "Weekly newsletter",
            "Transaction alert: $50 deposit",
        ]

        valuable, promotional, uncategorized = analyze_sender_email_patterns(subjects)

        assert len(valuable) == 3  # credit score, balance update, transaction alert
        assert len(promotional) == 2  # loan offer, newsletter
        assert len(uncategorized) == 0

    def test_generate_cleanup_report(self, sample_audit_data):
        """Test generating a cleanup report."""
        report = generate_cleanup_report(sample_audit_data)

        assert "EMAIL AUDIT REPORT" in report
        assert "5 senders, 63 emails" in report
        assert "TOP 10 NOISE MAKERS" in report
        assert "CLEANUP RECOMMENDATIONS" in report

    def test_generate_cleanup_report_with_baseline(self, sample_audit_data):
        """Test generating a cleanup report with baseline comparison."""
        report = generate_cleanup_report(sample_audit_data, BASELINE_METRICS)

        assert "IMPROVEMENT METRICS" in report
        assert "Unread Rate Improvement" in report
        assert "Top Score Reduction" in report

    def test_load_audit_data_file_not_found(self):
        """Test loading audit data when file doesn't exist."""
        df = load_audit_data("nonexistent_file.csv")

        assert df.empty

    def test_baseline_metrics_structure(self):
        """Test that baseline metrics has expected structure."""
        expected_keys = {"total_emails", "unread_percentage", "average_open_rate", "senders_never_opened", "top_ignorance_score"}

        assert set(BASELINE_METRICS.keys()) == expected_keys
        assert all(isinstance(v, (int, float)) for v in BASELINE_METRICS.values())
