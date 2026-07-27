"""Configuration management for murb-geometry.

Uses pydantic-settings for validated, typed configuration loaded from
YAML files with local override support.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class PathsConfig(BaseModel):
    """File system paths configuration."""

    data_dir: Path = Path("data")
    output_dir: Path = Path("outputs")
    raw_subdir: str = "raw"
    external_subdir: str = "external"
    interim_subdir: str = "interim"
    processed_subdir: str = "processed"
    samples_subdir: str = "samples"


class InputConfig(BaseModel):
    """Input data configuration."""

    file_patterns: list[str] = Field(default_factory=lambda: ["data/**/ODB_v3_*.gpkg"])
    missing_value_markers: list[str] = Field(default_factory=lambda: ["..", "", "NA", "N/A"])
    expected_crs: str = "EPSG:3347"
    target_projected_crs: str = "EPSG:3347"
    province_filter: list[str] | None = None


class StoreyBand(BaseModel):
    """A single storey-height band definition."""

    min: int
    max: int | None = None


class StoreyBandsConfig(BaseModel):
    """Storey classification bands."""

    low_rise_multifamily: StoreyBand = StoreyBand(min=2, max=3)
    small_mid_rise: StoreyBand = StoreyBand(min=4, max=6)
    large_mid_rise: StoreyBand = StoreyBand(min=7, max=12)
    low_high_rise: StoreyBand = StoreyBand(min=13, max=25)
    tall_high_rise: StoreyBand = StoreyBand(min=26, max=None)


class ClassificationConfig(BaseModel):
    """MURB classification parameters."""

    minimum_murb_units: int = 4
    confidence_levels: list[str] = Field(
        default_factory=lambda: [
            "confirmed_murb",
            "high_confidence_murb",
            "probable_murb",
            "possible_murb",
            "non_murb",
            "insufficient_information",
        ]
    )
    footprint_area: dict[str, float] = Field(
        default_factory=lambda: {
            "minimum_candidate_m2": 200.0,
            "maximum_plausible_m2": 50000.0,
        }
    )


class HeightAssumptionsConfig(BaseModel):
    """Height-to-storey conversion assumptions."""

    default_floor_to_floor_m: float = 3.0
    ground_floor_height_m: float = 3.5
    residential_floor_to_floor_m: float = 2.9
    commercial_ground_floor_m: float = 4.0


class GeometryConfig(BaseModel):
    """Geometry processing parameters."""

    simplification_tolerance_m: float = 0.5
    minimum_component_area_m2: float = 10.0
    facade_orientation_bins: dict[str, list[float]] | None = None


class ShapeClassificationConfig(BaseModel):
    """Shape classification thresholds."""

    rectangularity_threshold: float = 0.90
    elongation_threshold: float = 3.0
    convexity_threshold: float = 0.85
    courtyard_hole_fraction: float = 0.05


class OutlierConfig(BaseModel):
    """Outlier detection parameters."""

    method: str = "iqr"
    iqr_factor: float = 1.5
    zscore_threshold: float = 3.0
    percentile_lower: float = 0.5
    percentile_upper: float = 99.5


class ReproducibilityConfig(BaseModel):
    """Reproducibility settings."""

    random_seed: int = 42
    deterministic: bool = True


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "structured"


class ArchetypesConfig(BaseModel):
    """Archetype clustering parameters."""

    clustering_method: str = "kmeans"
    n_clusters: int = 8
    random_seed: int = 42
    clustering_features: list[str] = Field(
        default_factory=lambda: [
            "footprint_area_m2",
            "aspect_ratio",
            "floors",
            "compactness",
            "shape_class",
        ]
    )
    weighting_method: str | None = None


class WWRConfig(BaseModel):
    """Window-to-wall ratio assumptions."""

    default_north: float = 0.30
    default_east: float = 0.30
    default_south: float = 0.40
    default_west: float = 0.30
    source: str = "archetypal_assumption"
    note: str = "WWR cannot be derived from building footprints alone"


class GbxmlConfig(BaseModel):
    """gbXML export configuration."""

    schema_version: str = "7.03"
    length_unit: str = "Meters"
    area_unit: str = "SquareMeters"
    volume_unit: str = "CubicMeters"
    temperature_unit: str = "C"


class AppConfig(BaseSettings):
    """Root application configuration."""

    paths: PathsConfig = Field(default_factory=PathsConfig)
    input: InputConfig = Field(default_factory=InputConfig)
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)
    storey_bands: StoreyBandsConfig = Field(default_factory=StoreyBandsConfig)
    height_assumptions: HeightAssumptionsConfig = Field(default_factory=HeightAssumptionsConfig)
    geometry: GeometryConfig = Field(default_factory=GeometryConfig)
    shape_classification: ShapeClassificationConfig = Field(
        default_factory=ShapeClassificationConfig
    )
    outliers: OutlierConfig = Field(default_factory=OutlierConfig)
    archetypes: ArchetypesConfig = Field(default_factory=ArchetypesConfig)
    wwr: WWRConfig = Field(default_factory=WWRConfig)
    gbxml: GbxmlConfig = Field(default_factory=GbxmlConfig)
    reproducibility: ReproducibilityConfig = Field(default_factory=ReproducibilityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(
    config_path: str | Path = "config/default.yaml",
    local_path: str | Path | None = "config/local.yaml",
) -> AppConfig:
    """Load configuration from YAML files with local override.

    Parameters
    ----------
    config_path
        Path to the default configuration file.
    local_path
        Path to optional local override file. Set to None to skip.

    Returns
    -------
    AppConfig
        Validated application configuration.
    """
    config_data: dict[str, Any] = {}

    default_file = Path(config_path)
    if default_file.exists():
        with open(default_file) as f:
            config_data = yaml.safe_load(f) or {}

    if local_path is not None:
        local_file = Path(local_path)
        if local_file.exists():
            with open(local_file) as f:
                local_data = yaml.safe_load(f) or {}
            config_data = _deep_merge(config_data, local_data)

    return AppConfig(**config_data)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override dict into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
