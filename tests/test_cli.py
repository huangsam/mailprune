"""
Tests for mailprune CLI commands.
"""

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

# Add the src directory to the path so we can import mailprune
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from scripts.analyze_emails import cli


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_csv(tmp_path):
    """Create a temporary CSV file with sample data."""
    csv_content = """from,total_volume,open_rate,ignorance_score,unread_count
test@example.com,10,50.0,500,5
newsletter@company.com,25,10.0,2250,22
bank@bank.com,5,80.0,100,1
promo@store.com,15,0.0,1500,15
important@service.com,8,60.0,320,3
"""

    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


class TestCLICommands:
    """Test the CLI commands."""

    def test_metrics_command(self, runner, sample_csv):
        """Test the metrics command."""
        result = runner.invoke(cli, ["metrics", "--csv-path", sample_csv])

        assert result.exit_code == 0
        assert "Total Emails: 63" in result.output
        assert "Unread Rate: 73.0%" in result.output
        assert "Average Open Rate: 40.0%" in result.output
        assert "Senders Never Opened: 1" in result.output
        assert "Top Ignorance Score: 2250" in result.output

    def test_top_noise_command(self, runner, sample_csv):
        """Test the top-noise command."""
        result = runner.invoke(cli, ["top-noise", "--csv-path", sample_csv, "--n", "3"])

        assert result.exit_code == 0
        assert "TOP 3 NOISE MAKERS" in result.output
        assert "newsletter@company.com" in result.output
        assert "promo@store.com" in result.output
        assert "test@example.com" in result.output

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

    def test_progress_command(self, runner, sample_csv):
        """Test the progress command."""
        result = runner.invoke(cli, ["progress", "--csv-path", sample_csv])

        assert result.exit_code == 0
        assert "CLEANUP PROGRESS" in result.output
        assert "Unread Rate Improvement" in result.output
        assert "Top Score Reduction" in result.output
        assert "Open Rate Improvement" in result.output

    def test_report_command(self, runner, sample_csv):
        """Test the report command."""
        result = runner.invoke(cli, ["report", "--csv-path", sample_csv])

        assert result.exit_code == 0
        assert "EMAIL AUDIT REPORT" in result.output
        assert "Current Status: 5 senders, 63 emails" in result.output
        assert "IMPROVEMENT METRICS" in result.output
        assert "TOP 10 NOISE MAKERS" in result.output
        assert "CLEANUP RECOMMENDATIONS" in result.output

    def test_help_command(self, runner):
        """Test the help command."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Email analysis tools for mailprune audit data" in result.output
        assert "metrics" in result.output
        assert "progress" in result.output
        assert "report" in result.output
        assert "sender" in result.output
        assert "top-noise" in result.output
