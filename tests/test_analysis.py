"""
Tests for mailprune analysis functions.
"""

import pandas as pd
import pytest

from mailprune import (
    analyze_sender_email_patterns,
    analyze_sender_patterns,
    calculate_overall_metrics,
    cluster_senders_unsupervised,
    compare_metrics,
    generate_cleanup_report,
    get_top_noise_makers,
    infer_intent_nlp,
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

    def test_load_audit_data_file_not_found(self):
        """Test loading audit data when file doesn't exist."""
        df = load_audit_data("nonexistent_file.csv")

        assert df.empty

    def test_cluster_senders_unsupervised(self, sample_audit_data):
        """Test unsupervised clustering of senders."""
        clusters = cluster_senders_unsupervised(sample_audit_data, n_clusters=3)

        assert isinstance(clusters, dict)
        assert len(clusters) == len(sample_audit_data)
        assert all(isinstance(cluster_id, int) for cluster_id in clusters.values())
        assert all(cluster_id >= 0 and cluster_id < 3 for cluster_id in clusters.values())
        # Check that all senders are assigned
        assert set(clusters.keys()) == set(sample_audit_data["from"])

    def test_cluster_senders_unsupervised_empty_df(self):
        """Test clustering with empty dataframe."""
        empty_df = pd.DataFrame()
        clusters = cluster_senders_unsupervised(empty_df)
        assert clusters == {}

    def test_cluster_senders_unsupervised_few_senders(self, sample_audit_data):
        """Test clustering with fewer senders than clusters."""
        small_df = sample_audit_data.head(2)
        clusters = cluster_senders_unsupervised(small_df, n_clusters=5)
        assert clusters == {}

    def test_infer_intent_nlp(self):
        """Test intent inference using NLP."""
        # Test promotional content
        promo_text = "Buy now and save 50% on our limited time offer! Subscribe to our newsletter for exclusive deals."
        intent = infer_intent_nlp(promo_text, use_nlp=True)
        assert intent == "promotional"

        # Test transactional content
        trans_text = "Your order has been confirmed. Payment of $25.99 has been processed. Receipt attached."
        intent = infer_intent_nlp(trans_text, use_nlp=True)
        assert intent == "transactional"

        # Test informational content
        info_text = "Update: Your account status has changed. Please review the attached report."
        intent = infer_intent_nlp(info_text, use_nlp=True)
        assert intent == "informational"

        # Test unknown content
        unknown_text = "Hello, how are you doing today?"
        intent = infer_intent_nlp(unknown_text, use_nlp=True)
        assert intent == "unknown"

        # Test top N intents
        mixed_text = "Buy now and save! Your order is confirmed. Account update available."
        top_intents = infer_intent_nlp(mixed_text, use_nlp=True, top_n=3)
        assert isinstance(top_intents, list)
        assert len(top_intents) <= 3
        # Should have promotional and transactional as top intents
        intent_names = [intent for intent, score in top_intents]
        assert "promotional" in intent_names or "transactional" in intent_names

    def test_infer_intent_nlp_empty_text(self):
        """Test infer_intent_nlp with empty text."""
        result = infer_intent_nlp("", use_nlp=True)
        assert result == "unknown"

    def test_infer_intent_nlp_no_nlp(self):
        """Test infer_intent_nlp without NLP."""
        text = "Buy now and save 50%!"
        result = infer_intent_nlp(text, use_nlp=False)
        assert result == "unknown"  # Should fallback when NLP disabled

    def test_load_audit_data_invalid_format(self, tmp_path):
        """Test load_audit_data with invalid CSV format."""
        invalid_csv = tmp_path / "invalid.csv"
        invalid_csv.write_text("not,a,valid,csv,format\nwith,wrong,number,of,cols\n")

        result = load_audit_data(str(invalid_csv))
        # Should handle gracefully and return empty or partial DataFrame
        assert isinstance(result, pd.DataFrame)

    def test_analyze_sender_email_patterns_missing_data(self):
        """Test analyze_sender_email_patterns with missing email data."""
        result = analyze_sender_email_patterns([])
        assert isinstance(result, tuple)
        assert len(result) == 3  # Should return three lists
