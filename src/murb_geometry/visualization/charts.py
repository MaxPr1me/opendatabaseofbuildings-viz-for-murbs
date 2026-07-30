"""Figure generation from persisted MURB outputs.

Builds figures from validated pipeline artifacts only — the run manifest, the
pathway-sensitivity report, and the persisted MURB subsets (via the datastore).
Nothing is re-derived from raw data here. Static PNG export is best-effort
(requires the optional ``kaleido`` package); interactive HTML is always written.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from murb_geometry import datastore

logger = logging.getLogger(__name__)

# Positive-MURB confidence tiers, strongest first.
POSITIVE_TIERS = ["confirmed_murb", "high_confidence_murb", "probable_murb", "possible_murb"]
_TIER_COLORS = {
    "confirmed_murb": "#1a9850",
    "high_confidence_murb": "#66bd63",
    "probable_murb": "#fdae61",
    "possible_murb": "#f46d43",
}


def _write(fig: go.Figure, output_dir: Path, name: str) -> Path:
    """Write a figure to HTML (always) and PNG (best-effort)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / f"{name}.html"
    fig.write_html(str(html_path))
    try:
        fig.write_image(str(output_dir / f"{name}.png"), scale=2)
    except Exception as exc:
        # PNG export is optional (requires the kaleido package); HTML is always written.
        logger.warning("PNG export skipped for %s (%s); HTML written", name, exc)
    return html_path


def counts_by_province(manifest: dict[str, Any]) -> go.Figure:
    """Grouped bar of precision vs tiered MURB counts per province."""
    prov = manifest["stages"]["province_processing"]
    rows = [
        {"province": p, "pathway": "precision", "count": d.get("precision_count", 0)}
        for p, d in prov.items()
    ] + [
        {"province": p, "pathway": "tiered", "count": d.get("tiered_count", 0)}
        for p, d in prov.items()
    ]
    df = pd.DataFrame(rows)
    df = df[df["count"] > 0]
    fig = px.bar(
        df,
        x="province",
        y="count",
        color="pathway",
        barmode="group",
        title="MURB counts by province and pathway",
        labels={"count": "Buildings", "province": "Province"},
        color_discrete_map={"precision": "#1a9850", "tiered": "#fdae61"},
    )
    fig.update_layout(width=900, height=500)
    return fig


def classification_by_province(manifest: dict[str, Any]) -> go.Figure:
    """Stacked bar of positive-tier classification counts per province."""
    prov = manifest["stages"]["province_processing"]
    rows: list[dict[str, Any]] = []
    for p, d in prov.items():
        cls = d.get("classification_summary", {})
        for tier in POSITIVE_TIERS:
            rows.append({"province": p, "confidence": tier, "count": cls.get(tier, 0)})
    df = pd.DataFrame(rows)
    df = df[df["count"] > 0]
    fig = px.bar(
        df,
        x="province",
        y="count",
        color="confidence",
        title="Positive-MURB classification by province (tiered pathway)",
        labels={"count": "Buildings", "province": "Province"},
        category_orders={"confidence": POSITIVE_TIERS},
        color_discrete_map=_TIER_COLORS,
    )
    fig.update_layout(width=900, height=500)
    return fig


def metric_distribution_by_confidence(
    df: pd.DataFrame,
    metric: str,
    title: str,
    y_label: str,
) -> go.Figure:
    """Box plot of a geometry metric grouped by confidence level."""
    present = [t for t in POSITIVE_TIERS if t in set(df.get("confidence_level", []))]
    fig = px.box(
        df[df[metric].notna()],
        x="confidence_level",
        y=metric,
        color="confidence_level",
        title=title,
        labels={metric: y_label, "confidence_level": "Confidence"},
        category_orders={"confidence_level": present},
        color_discrete_map=_TIER_COLORS,
    )
    fig.update_layout(width=900, height=500, showlegend=False)
    return fig


def build_all_figures(
    output_dir: Path | None = None,
    reports_dir: Path | None = None,
) -> list[Path]:
    """Regenerate all figures from persisted outputs. Returns written HTML paths.

    Requires a completed run (``murb-geometry run-all``): the run manifest and the
    tiered MURB subset must exist.
    """
    output_dir = output_dir or Path("outputs/figures")
    reports_dir = reports_dir or Path("outputs/reports")
    manifest_path = reports_dir / "run_manifest.json"
    if not manifest_path.exists():
        msg = f"Run manifest not found at {manifest_path}. Run `murb-geometry run-all` first."
        raise FileNotFoundError(msg)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    written: list[Path] = []

    written.append(_write(counts_by_province(manifest), output_dir, "counts_by_province"))
    written.append(
        _write(classification_by_province(manifest), output_dir, "classification_by_province")
    )

    if datastore.subset_available("tiered"):
        tiered = datastore.load_murb_subset("tiered", drop_geometry=True)
        if "footprint_area_m2" in tiered.columns:
            written.append(
                _write(
                    metric_distribution_by_confidence(
                        tiered, "footprint_area_m2", "Footprint area by confidence", "Area (m²)"
                    ),
                    output_dir,
                    "footprint_area_by_confidence",
                )
            )
        if "aspect_ratio" in tiered.columns:
            written.append(
                _write(
                    metric_distribution_by_confidence(
                        tiered, "aspect_ratio", "Aspect ratio by confidence", "Aspect ratio"
                    ),
                    output_dir,
                    "aspect_ratio_by_confidence",
                )
            )

    logger.info("Wrote %d figures to %s", len(written), output_dir)
    return written
