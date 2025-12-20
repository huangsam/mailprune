"""
Tests for mailprune CLI commands.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import mailprune
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest  # noqa: E402
from click.testing import CliRunner  # noqa: E402

from scripts.mailprune import cli  # noqa: E402


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

    def test_unread_by_category_command(self, runner, sample_csv):
        """Test the unread-by-category command."""
        result = runner.invoke(cli, ["unread-by-category", "--csv-path", sample_csv])

        assert result.exit_code == 0
        assert "UNREAD EMAILS BY CATEGORY" in result.output
        assert "Total Unread Emails: 46 out of 63" in result.output
        assert "CLEANUP RECOMMENDATIONS FOR UNREAD EMAILS" in result.output
        assert "PROMOTIONS" in result.output
        assert "UPDATES" in result.output
        assert "IMPORTANT" in result.output

    def test_help_command(self, runner):
        """Test the help command."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "MailPrune - Email Audit and Analysis Tool" in result.output
        assert "audit" in result.output
        assert "report" in result.output
        assert "sender" in result.output
        assert "unread-by-category" in result.output
