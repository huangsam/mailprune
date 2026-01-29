"""
Tests for mailprune CLI commands.
"""

from unittest.mock import Mock, patch

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


class TestCLIAuth:
    """Test CLI authentication commands."""

    def test_auth_command_missing_credentials(self, runner, tmp_path, monkeypatch):
        """Test auth command when credentials file doesn't exist."""
        # Change to temp directory without credentials
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(cli, ["auth"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()
        assert "credentials" in result.output.lower()

    def test_auth_command_token_exists_no_confirm(self, runner, tmp_path, monkeypatch):
        """Test auth command when token exists and user declines overwrite."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create fake credentials and token files
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text('{"fake": "credentials"}')

        token_file = tmp_path / "token.json"
        token_file.write_text('{"fake": "token"}')

        # Mock click.confirm to return False (user declines)
        with patch("click.confirm", return_value=False):
            result = runner.invoke(cli, ["auth"])

        # Should exit without doing anything (click.confirm abort=True)
        assert result.exit_code == 1

    @patch("mailprune.cli.InstalledAppFlow.from_client_secrets_file")
    @patch("mailprune.cli.os.path.exists")
    def test_auth_command_success(self, mock_exists, mock_flow_from_file, runner, tmp_path, monkeypatch):
        """Test successful auth command execution."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create data directory and fake credentials file
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        creds_file = data_dir / "credentials.json"
        creds_file.write_text('{"fake": "credentials"}')

        # Mock file existence checks - credentials exist, token doesn't
        def mock_exists_func(path):
            if "data/credentials.json" in str(path):
                return True
            elif "data/token.json" in str(path):
                return False
            return True

        mock_exists.side_effect = mock_exists_func

        # Mock the flow and credentials
        mock_flow = Mock()
        mock_creds = Mock()
        mock_creds.to_json.return_value = '{"access_token": "fake_token"}'
        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_from_file.return_value = mock_flow

        result = runner.invoke(cli, ["auth"])

        assert result.exit_code == 0
        assert "Authentication successful" in result.output
        assert "Token saved" in result.output

    @patch("mailprune.cli.InstalledAppFlow.from_client_secrets_file")
    @patch("mailprune.cli.os.path.exists")
    def test_auth_command_flow_failure(self, mock_exists, mock_flow_from_file, runner, tmp_path, monkeypatch):
        """Test auth command when authentication flow fails."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create data directory and fake credentials file
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        creds_file = data_dir / "credentials.json"
        creds_file.write_text('{"fake": "credentials"}')

        # Mock file existence checks - credentials exist, token doesn't
        def mock_exists_func(path):
            if "data/credentials.json" in str(path):
                return True
            elif "data/token.json" in str(path):
                return False
            return True

        mock_exists.side_effect = mock_exists_func

        # Mock the flow to raise an exception
        mock_flow = Mock()
        mock_flow.run_local_server.side_effect = Exception("Network error")
        mock_flow_from_file.return_value = mock_flow

        result = runner.invoke(cli, ["auth"])

        assert result.exit_code == 1
        assert "Authentication failed" in result.output


class TestCommandExecution:
    """Test actual command execution logic (not just CLI interface)."""

    @patch("mailprune.commands.patterns.analyze_title_patterns_core")
    def test_patterns_command_execution_success(self, mock_analyze, runner, tmp_path):
        """Test successful patterns command execution."""
        # Mock the analysis function
        mock_analyze.return_value = {
            "sender1@example.com": {
                "sample_subject": "Test Subject",
                "email_count": 5,
                "nlp_used": True,
                "top_intents": [("promotional", 0.8), ("transactional", 0.2)],
                "top_keywords": [("test", 3), ("email", 2)],
                "top_entities": {"ORG": [("Company", 2)]},
            }
        }

        # Create mock cache and CSV files
        cache_file = tmp_path / "email_cache.json"
        cache_file.write_text('{"msg1": {"snippet": "test content"}}')

        csv_file = tmp_path / "data.csv"
        csv_file.write_text("from,total_volume\nsender1@example.com,10\n")

        result = runner.invoke(cli, ["patterns", "--cache-path", str(cache_file), "--csv-path", str(csv_file), "--top-n", "1"])

        assert result.exit_code == 0
        assert "Content Pattern Analysis" in result.output
        assert "sender1@example.com" in result.output
        assert "promotional (0.8)" in result.output
        mock_analyze.assert_called_once()

    @patch("mailprune.commands.patterns.analyze_title_patterns_core")
    def test_patterns_command_execution_no_nlp(self, mock_analyze, runner, tmp_path):
        """Test patterns command execution without NLP."""
        mock_analyze.return_value = {
            "sender1@example.com": {"sample_subject": "Test Subject", "email_count": 3, "nlp_used": False, "top_keywords": [("test", 2)]}
        }

        # Create mock files
        cache_file = tmp_path / "email_cache.json"
        cache_file.write_text('{"msg1": {"snippet": "test"}}')

        csv_file = tmp_path / "data.csv"
        csv_file.write_text("from,total_volume\nsender1@example.com,5\n")

        result = runner.invoke(cli, ["patterns", "--cache-path", str(cache_file), "--csv-path", str(csv_file), "--no-nlp"])

        assert result.exit_code == 0
        assert "NLP Processing: Disabled" in result.output

    def test_engagement_command_execution(self, runner, sample_csv):
        """Test engagement command execution logic."""
        result = runner.invoke(cli, ["engagement", "--csv-path", sample_csv])

        assert result.exit_code == 0
        assert "ENGAGEMENT ANALYSIS" in result.output
        assert "Total Emails:" in result.output

    def test_cluster_command_execution(self, runner, sample_csv):
        """Test cluster command execution logic."""
        result = runner.invoke(cli, ["cluster", "--csv-path", sample_csv, "--n-clusters", "2"])

        assert result.exit_code == 0
        assert "UNSUPERVISED SENDER CLUSTERING" in result.output


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""

    def test_cli_verbose_flag(self, runner):
        """Test CLI verbose flag functionality."""
        result = runner.invoke(cli, ["--help", "--verbose"])

        # Should still work normally, verbose flag just enables logging
        assert result.exit_code == 0
        assert "Mailprune" in result.output

    def test_audit_command_invalid_max_emails(self, runner, tmp_path, monkeypatch):
        """Test audit command with invalid max_emails parameter."""
        # Change to temp directory without credentials
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(cli, ["audit", "--max-emails", "invalid"])

        # Click should handle parameter validation
        assert result.exit_code == 2  # Click parameter error
        assert "Invalid value" in result.output

    def test_report_command_invalid_brief_flag(self, runner, sample_csv):
        """Test report command with invalid flag usage."""
        # --brief doesn't take arguments, this should fail
        result = runner.invoke(cli, ["report", "--brief", "invalid", "--csv-path", sample_csv])

        assert result.exit_code == 2
        assert "Error" in result.output or "Invalid" in result.output

    def test_sender_command_no_sender_arg(self, runner, sample_csv):
        """Test sender command without required sender argument."""
        result = runner.invoke(cli, ["sender", "--csv-path", sample_csv])

        assert result.exit_code == 2
        assert "Missing argument" in result.output

    def test_patterns_command_missing_cache(self, runner, sample_csv):
        """Test patterns command with missing cache file."""
        result = runner.invoke(cli, ["patterns", "--cache-path", "nonexistent.json", "--csv-path", sample_csv])

        # Should handle gracefully
        assert result.exit_code == 0  # Commands handle errors gracefully

    def test_engagement_command_invalid_tier(self, runner, sample_csv):
        """Test engagement command with invalid tier parameter."""
        result = runner.invoke(cli, ["engagement", "--csv-path", sample_csv, "--tier", "invalid"])

        # Should handle gracefully or show error
        assert result.exit_code in [0, 2]  # Either handles gracefully or shows parameter error

    def test_cluster_command_invalid_clusters(self, runner, sample_csv):
        """Test cluster command with invalid n_clusters parameter."""
        result = runner.invoke(cli, ["cluster", "--csv-path", sample_csv, "--n-clusters", "0"])

        # sklearn raises InvalidParameterError for n_clusters=0
        assert result.exit_code == 1
