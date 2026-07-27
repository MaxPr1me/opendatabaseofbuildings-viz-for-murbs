"""Unit tests for CLI commands (smoke tests)."""

from typer.testing import CliRunner

from murb_geometry.cli import app

runner = CliRunner()


def test_cli_help() -> None:
    """CLI shows help without error."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "murb-geometry" in result.stdout.lower() or "Canadian" in result.stdout


def test_inventory_command_planned() -> None:
    """Inventory command exits cleanly with planned message."""
    result = runner.invoke(app, ["inventory"])
    assert result.exit_code == 0
    assert "planned" in result.stdout.lower()


def test_inspect_command_planned() -> None:
    """Inspect command exits cleanly with planned message."""
    result = runner.invoke(app, ["inspect", "dummy.gpkg"])
    assert result.exit_code == 0
    assert "planned" in result.stdout.lower()
