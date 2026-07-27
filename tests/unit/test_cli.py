"""Unit tests for CLI commands (smoke tests)."""

from typer.testing import CliRunner

from murb_geometry.cli import app

runner = CliRunner()


def test_cli_help() -> None:
    """CLI shows help without error."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "murb-geometry" in result.stdout.lower() or "Canadian" in result.stdout


def test_inspect_command_missing_file() -> None:
    """Inspect command fails with non-existent file."""
    result = runner.invoke(app, ["inspect", "nonexistent.gpkg"])
    assert result.exit_code == 1
