"""Shared test fixtures for murb-geometry."""

from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def config_dir(project_root: Path) -> Path:
    """Return the config directory."""
    return project_root / "config"


@pytest.fixture
def sample_config_path(config_dir: Path) -> Path:
    """Return the default configuration file path."""
    return config_dir / "default.yaml"
