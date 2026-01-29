"""
Tests for mailprune utility functions.
"""

import json

import pandas as pd
import pytest

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
