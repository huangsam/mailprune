"""
Tests for mailprune utility functions.
"""

import json

import pandas as pd
import pytest

from mailprune.utils.audit import (
    aggregate_and_score,
    get_sender_snippets_from_cache,
    get_sender_subjects_from_cache,
    prune_cache,
)
from mailprune.utils.helpers import (
    calculate_percentage,
    format_sender_list,
    get_category_distribution,
    get_engagement_tier_names,
    load_email_cache,
    save_email_cache,
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


class TestHelperFunctions:
    """Test helper utility functions."""

    def test_calculate_percentage(self):
        """Test percentage calculation formatting."""
        assert calculate_percentage(25, 100) == "25.0%"
        assert calculate_percentage(1, 3) == "33.3%"
        assert calculate_percentage(0, 100) == "0.0%"
        assert calculate_percentage(0, 0) == "0.0%"  # Edge case: division by zero

    def test_get_engagement_tier_names(self):
        """Test engagement tier name mapping."""
        tiers = get_engagement_tier_names()
        assert isinstance(tiers, dict)
        assert "high" in tiers
        assert "medium" in tiers
        assert "low" in tiers
        assert "zero" in tiers
        assert "High Engagement" in tiers["high"]
        assert "Zero Engagement" in tiers["zero"]

    def test_format_sender_list(self, sample_audit_data):
        """Test sender list formatting with truncation."""
        formatted = format_sender_list(sample_audit_data.head(2))
        assert len(formatted) == 2
        assert "test@example.com" in formatted[0]
        assert "emails" in formatted[0]
        assert "open" in formatted[0]

        # Test with custom max length
        formatted_short = format_sender_list(sample_audit_data.head(1), max_name_length=10)
        assert len(formatted_short[0].split("|")[0].strip()) <= 10

    def test_get_category_distribution(self, sample_audit_data):
        """Test category distribution calculation."""
        # Add category columns to sample data
        sample_data_with_categories = sample_audit_data.copy()
        sample_data_with_categories["updates_count"] = [8, 20, 0, 0, 2]
        sample_data_with_categories["promotions_count"] = [2, 5, 0, 15, 0]
        sample_data_with_categories["social_count"] = [0, 0, 0, 0, 0]
        sample_data_with_categories["important_count"] = [0, 0, 5, 0, 6]

        total_emails = sample_data_with_categories["total_volume"].sum()
        distribution = get_category_distribution(sample_data_with_categories, total_emails)

        assert isinstance(distribution, list)
        assert len(distribution) > 0
        assert any("Updates" in line for line in distribution)
        assert any("Promotions" in line for line in distribution)
        assert any("Important" in line for line in distribution)
        # Social should not appear since it's 0
        assert not any("Social" in line for line in distribution)

    def test_load_email_cache_file_exists(self, tmp_path):
        """Test loading cache when file exists."""
        cache_file = tmp_path / "test_cache.json"
        test_data = {"sender@example.com": {"subjects": ["Test Subject"]}}
        cache_file.write_text('{"sender@example.com": {"subjects": ["Test Subject"]}}')

        result = load_email_cache(str(cache_file))
        assert result == test_data

    def test_load_email_cache_file_not_found(self, tmp_path):
        """Test loading cache when file doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.json"
        result = load_email_cache(str(nonexistent_file))
        assert result == {}

    def test_load_email_cache_invalid_json(self, tmp_path):
        """Test loading cache with invalid JSON."""
        cache_file = tmp_path / "invalid.json"
        cache_file.write_text("invalid json content")

        result = load_email_cache(str(cache_file))
        assert result == {}  # Should return empty dict on error

    def test_save_email_cache(self, tmp_path):
        """Test saving email cache to file."""
        cache_file = tmp_path / "test_save.json"
        test_data = {"sender@example.com": {"subjects": ["Test Subject"]}}

        save_email_cache(test_data, str(cache_file))

        # Verify file was created and contains correct data
        assert cache_file.exists()
        with open(cache_file) as f:
            saved_data = json.load(f)
        assert saved_data == test_data


class TestAuditUtils:
    """Test audit utility functions."""

    def test_get_sender_subjects_from_cache(self):
        """Test extracting sender-subject mapping from cache."""
        mock_cache = {
            "msg1": {"payload": {"headers": [{"name": "From", "value": "sender1@example.com"}, {"name": "Subject", "value": "Test Subject 1"}]}},
            "msg2": {"payload": {"headers": [{"name": "From", "value": "sender1@example.com"}, {"name": "Subject", "value": "Test Subject 2"}]}},
            "msg3": {"payload": {"headers": [{"name": "From", "value": "sender2@example.com"}, {"name": "Subject", "value": "Different Subject"}]}},
        }

        result = get_sender_subjects_from_cache(mock_cache)

        assert "sender1@example.com" in result
        assert "sender2@example.com" in result
        assert len(result["sender1@example.com"]) == 2
        assert len(result["sender2@example.com"]) == 1
        assert "Test Subject 1" in result["sender1@example.com"]
        assert "Test Subject 2" in result["sender1@example.com"]
        assert "Different Subject" in result["sender2@example.com"]

    def test_get_sender_subjects_from_cache_missing_headers(self):
        """Test handling cache entries with missing headers."""
        mock_cache = {
            "msg1": {
                "payload": {
                    "headers": [
                        {"name": "From", "value": "sender@example.com"}
                        # Missing Subject header
                    ]
                }
            },
            "msg2": {
                "payload": {}  # Missing headers entirely
            },
        }

        result = get_sender_subjects_from_cache(mock_cache)

        assert "sender@example.com" in result
        assert len(result["sender@example.com"]) == 1
        assert result["sender@example.com"][0] == ""  # Empty subject

    def test_get_sender_snippets_from_cache(self):
        """Test extracting sender-snippet mapping from cache."""
        mock_cache = {
            "msg1": {"payload": {"headers": [{"name": "From", "value": "sender1@example.com"}]}, "snippet": "This is a test email snippet"},
            "msg2": {"payload": {"headers": [{"name": "From", "value": "sender1@example.com"}]}, "snippet": "Another snippet from same sender"},
            "msg3": {
                "payload": {"headers": [{"name": "From", "value": "sender2@example.com"}]},
                "snippet": "",  # Empty snippet should be ignored
            },
        }

        result = get_sender_snippets_from_cache(mock_cache)

        assert "sender1@example.com" in result
        assert "sender2@example.com" not in result  # Empty snippet ignored
        assert len(result["sender1@example.com"]) == 2
        assert "This is a test email snippet" in result["sender1@example.com"]
        assert "Another snippet from same sender" in result["sender1@example.com"]

    def test_aggregate_and_score(self):
        """Test aggregating email data and calculating ignorance scores."""
        # Create mock email data
        mock_df = pd.DataFrame(
            {
                "from": ["sender1@example.com", "sender1@example.com", "sender2@example.com", "sender2@example.com", "sender2@example.com"],
                "id": ["id1", "id2", "id3", "id4", "id5"],
                "unread": [True, False, True, True, False],
                "starred": [False, True, False, False, False],
                "important": [False, False, True, False, False],
                "social": [False, False, False, True, False],
                "updates": [True, False, False, False, False],
                "promotions": [False, False, False, False, True],
                "age_days": [1.0, 2.0, 1.5, 3.0, 2.5],
            }
        )

        result = aggregate_and_score(mock_df)

        # Check sender1 aggregation
        sender1_data = result[result["from"] == "sender1@example.com"].iloc[0]
        assert sender1_data["total_volume"] == 2
        assert sender1_data["unread_count"] == 1  # One unread email
        assert sender1_data["starred_count"] == 1
        assert sender1_data["important_count"] == 0
        assert sender1_data["social_count"] == 0
        assert sender1_data["updates_count"] == 1
        assert sender1_data["promotions_count"] == 0
        assert sender1_data["open_rate"] == 50.0  # 1 out of 2 emails opened
        assert sender1_data["ignorance_score"] == 100.0  # 2 * (100 - 50)

        # Check sender2 aggregation
        sender2_data = result[result["from"] == "sender2@example.com"].iloc[0]
        assert sender2_data["total_volume"] == 3
        assert sender2_data["unread_count"] == 2  # Two unread emails
        assert sender2_data["open_rate"] == pytest.approx(33.33, rel=1e-2)
        assert sender2_data["ignorance_score"] == pytest.approx(200.0, rel=1e-2)  # 3 * (100 - 33.33)

    def test_aggregate_and_score_empty_df(self):
        """Test aggregate_and_score with empty DataFrame."""
        empty_df = pd.DataFrame(columns=["from", "id", "unread", "starred", "important", "social", "updates", "promotions", "age_days"])
        result = aggregate_and_score(empty_df)
        assert len(result) == 0

    def test_prune_cache(self):
        """Test pruning removed emails from cache."""
        mock_cache = {
            "msg1": {"data": "email1"},
            "msg2": {"data": "email2"},
            "msg3": {"data": "email3"},
        }
        current_ids = {"msg1", "msg3"}  # msg2 was deleted

        pruned_count = prune_cache(mock_cache, current_ids)

        assert pruned_count == 1
        assert "msg1" in mock_cache
        assert "msg2" not in mock_cache  # Should be removed
        assert "msg3" in mock_cache

    def test_prune_cache_no_pruning_needed(self):
        """Test prune_cache when all emails still exist."""
        mock_cache = {
            "msg1": {"data": "email1"},
            "msg2": {"data": "email2"},
        }
        current_ids = {"msg1", "msg2", "msg3"}  # All cache emails still exist

        pruned_count = prune_cache(mock_cache, current_ids)

        assert pruned_count == 0
        assert len(mock_cache) == 2  # No change
