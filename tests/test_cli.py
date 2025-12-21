"""
Tests for mailprune CLI commands.
"""

import pytest
from click.testing import CliRunner

from mailprune.cli import cli


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_csv(tmp_path):
    """Create a temporary CSV file with sample data including category counts."""
    csv_content = """from,total_volume,open_rate,ignorance_score,unread_count,updates_count,promotions_count,social_count,important_count
test@example.com,10,50.0,500,5,8,2,0,0
newsletter@company.com,25,10.0,2250,22,20,5,0,0
bank@bank.com,5,80.0,100,1,0,0,0,5
promo@store.com,15,0.0,1500,15,0,15,0,0
important@service.com,8,60.0,320,3,2,0,0,6
"""

    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


class TestCLICommands:
    """Test the CLI commands."""

    def test_sender_command_found(self, runner, sample_csv):
        """Test the sender command with a found sender."""
        result = runner.invoke(cli, ["sender", "newsletter", "--csv-path", sample_csv])

        assert result.exit_code == 0
        assert "newsletter@company.com" in result.output
        assert "Total Emails: 25" in result.output
        assert "Open Rate: 10.0%" in result.output
        assert "Ignorance Score: 2250" in result.output

    def test_sender_command_not_found(self, runner, sample_csv):
        """Test the sender command with a sender not found."""
        result = runner.invoke(cli, ["sender", "nonexistent", "--csv-path", sample_csv])

        assert result.exit_code == 0
        assert "Sender 'nonexistent' not found" in result.output

    def test_report_command(self, runner, sample_csv):
        """Test the report command."""
        result = runner.invoke(cli, ["report", "--csv-path", sample_csv])

        assert result.exit_code == 0
        assert "COMPREHENSIVE EMAIL AUDIT REPORT" in result.output
        assert "5 unique senders" in result.output
        assert "63 total emails" in result.output
        assert "TOP 10 NOISE MAKERS" in result.output
        assert "CLEANUP RECOMMENDATIONS" in result.output

    def test_report_brief_command(self, runner, sample_csv):
        """Test the report command with --brief flag."""
        result = runner.invoke(cli, ["report", "--brief", "--csv-path", sample_csv])

        assert result.exit_code == 0
        assert "EMAIL AUDIT SUMMARY" in result.output
        assert "5 unique senders" in result.output
        assert "63 total emails" in result.output
        assert "TOP PRIORITIES" in result.output
        # Should not contain full report sections
        assert "COMPREHENSIVE EMAIL AUDIT REPORT" not in result.output
        assert "TOP 10 NOISE MAKERS" not in result.output

    def test_help_command(self, runner):
        """Test the help command."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Mailprune - Email Audit and Analysis Tool" in result.output
        assert "audit" in result.output
        assert "report" in result.output
        assert "sender" in result.output

    def test_audit_command_missing_credentials(self, runner, tmp_path, monkeypatch):
        """Test the audit command when credentials are missing."""
        # Change to temp directory without credentials
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(cli, ["audit", "--max-emails", "10"])

        # Should exit with error code when credentials are missing
        assert result.exit_code == 1
        assert "Failed to perform audit" in result.output
        assert "credentials" in result.output.lower()

    def test_patterns_command_no_data(self, runner, tmp_path):
        """Test the patterns command when no audit data exists."""
        # Create empty data directory
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        empty_csv = data_dir / "noise_report.csv"
        empty_csv.write_text("from,total_volume,open_rate,ignorance_score,unread_count\n")

        result = runner.invoke(cli, ["patterns", "--csv-path", str(empty_csv)])

        assert result.exit_code == 0
        assert "No audit data found" in result.output

    def test_patterns_command_with_data(self, runner, sample_csv, tmp_path):
        """Test the patterns command with valid data."""
        # Create a mock cache file
        cache_dir = tmp_path / "data"
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / "email_cache.json"
        cache_file.write_text('{"test@example.com": {"subjects": ["Test Subject"], "bodies": ["Test body content"]}}')

        result = runner.invoke(cli, ["patterns", "--csv-path", sample_csv, "--cache-path", str(cache_file), "--top-n", "2"])

        assert result.exit_code == 0
        assert "Content Pattern Analysis" in result.output

    def test_engagement_command(self, runner, sample_csv):
        """Test the engagement command."""
        result = runner.invoke(cli, ["engagement", "--csv-path", sample_csv])

        assert result.exit_code == 0
        assert "ENGAGEMENT ANALYSIS" in result.output
        assert "engagement" in result.output.lower()

    def test_engagement_command_specific_tier(self, runner, sample_csv):
        """Test the engagement command with specific tier filter."""
        result = runner.invoke(cli, ["engagement", "--csv-path", sample_csv, "--tier", "high"])

        assert result.exit_code == 0
        assert "HIGH ENGAGEMENT" in result.output

    def test_cluster_command(self, runner, sample_csv):
        """Test the cluster command."""
        result = runner.invoke(cli, ["cluster", "--csv-path", sample_csv, "--n-clusters", "3"])

        assert result.exit_code == 0
        assert "UNSUPERVISED SENDER CLUSTERING" in result.output
        assert "CLUSTER" in result.output

    def test_cluster_command_insufficient_data(self, runner, tmp_path):
        """Test the cluster command with insufficient data."""
        # Create CSV with only 1 sender
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        small_csv = data_dir / "noise_report.csv"
        small_csv.write_text("from,total_volume,open_rate,ignorance_score,unread_count\ntest@example.com,5,50.0,100,2\n")

        result = runner.invoke(cli, ["cluster", "--csv-path", str(small_csv), "--n-clusters", "3"])

        # Should still work but may show warnings
        assert result.exit_code == 0

    # Error scenario tests
    def test_report_command_file_not_found(self, runner):
        """Test the report command with non-existent file."""
        result = runner.invoke(cli, ["report", "--csv-path", "nonexistent.csv"])

        # Commands handle missing files gracefully
        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_sender_command_file_not_found(self, runner):
        """Test the sender command with non-existent file."""
        result = runner.invoke(cli, ["sender", "test", "--csv-path", "nonexistent.csv"])

        # Commands handle missing files gracefully
        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_patterns_command_invalid_csv(self, runner, tmp_path):
        """Test the patterns command with malformed CSV."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        invalid_csv = data_dir / "noise_report.csv"
        invalid_csv.write_text("invalid,csv,data\nnot,enough,columns\n")

        result = runner.invoke(cli, ["patterns", "--csv-path", str(invalid_csv)])

        # Should handle gracefully
        assert result.exit_code == 0  # Commands handle errors gracefully

    def test_cluster_command_empty_csv(self, runner, tmp_path):
        """Test the cluster command with empty CSV."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        empty_csv = data_dir / "noise_report.csv"
        empty_csv.write_text("from,total_volume,open_rate,ignorance_score,unread_count\n")

        result = runner.invoke(cli, ["cluster", "--csv-path", str(empty_csv)])

        assert result.exit_code == 0
        assert "No audit data found" in result.output
