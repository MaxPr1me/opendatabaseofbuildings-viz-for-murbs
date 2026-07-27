"""Unit tests for configuration loading."""

from pathlib import Path

from murb_geometry.config import AppConfig, load_config


def test_default_config_loads(sample_config_path: Path) -> None:
    """Default configuration file loads without errors."""
    config = load_config(config_path=sample_config_path, local_path=None)
    assert isinstance(config, AppConfig)


def test_default_config_has_expected_crs(sample_config_path: Path) -> None:
    """Default config specifies EPSG:3347."""
    config = load_config(config_path=sample_config_path, local_path=None)
    assert config.input.expected_crs == "EPSG:3347"


def test_default_config_storey_bands(sample_config_path: Path) -> None:
    """Storey bands are properly configured."""
    config = load_config(config_path=sample_config_path, local_path=None)
    assert config.storey_bands.small_mid_rise.min == 4
    assert config.storey_bands.small_mid_rise.max == 6


def test_config_missing_file_returns_defaults() -> None:
    """Loading a non-existent config file returns default values."""
    config = load_config(config_path="nonexistent.yaml", local_path=None)
    assert isinstance(config, AppConfig)
    assert config.reproducibility.random_seed == 42
