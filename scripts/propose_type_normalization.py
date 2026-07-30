"""Propose a `type` normalization mapping (DRAFT) grounded in observed values.

Reads the audited distinct-value inventory (outputs/reports/type_mapping_worksheet.csv)
and assigns each observed source `type` value to a normalized category using explicit,
documented keyword rules. Emits a DRAFT mapping for human sign-off. It does NOT modify
the classifier or active config.

MURB definition applied (owner decision, 2026-07-30):
    NBC Part 3 multi-unit residential = 4+ storeys (or > 600 m2 building area).
    Part 9 low-rise (duplex, semi-detached, townhouse, row, two-unit, single-family)
    is NOT a MURB. Therefore only explicit apartment / multi-residential / condominium
    TYPE values are positive MURB evidence from type alone; generic "residential" is
    context only and requires storey/height/unit evidence to qualify.

Outputs:
    config/type_normalization.yaml             — active mapping loaded by the classifier
    outputs/reports/type_mapping_proposed.csv  — every observed value + proposed category

Usage:
    python scripts/propose_type_normalization.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import yaml

WORKSHEET = Path("outputs/reports/type_mapping_worksheet.csv")
OUT_YAML = Path("config/type_normalization.yaml")
OUT_CSV = Path("outputs/reports/type_mapping_proposed.csv")

# Record count above which a value is also listed in the human-readable
# `reviewed_high_frequency` block (owner reviewed these explicitly).
REVIEWED_MIN_COUNT = 100

# Categories that count as POSITIVE MURB evidence from TYPE ALONE (Part 3 apartment scale).
MURB_POSITIVE = ("apartment", "multi_residential", "condominium")

# Categories that are explicitly NOT MURB (Part 9 low-rise / non-residential).
NON_MURB_CATEGORIES = (
    "residential_single",
    "low_rise_residential",
    "commercial",
    "industrial",
    "institutional",
    "other",
)

# Categories that are residential CONTEXT only (need storey/height/unit evidence).
CONTEXT_CATEGORIES = ("residential", "mixed_use")

# Ordered keyword rules. First match wins. Patterns are matched case-insensitively
# against the trimmed source value. French and English tokens are both included.
# Each tuple: (category, regex).
RULES: list[tuple[str, str]] = [
    # --- Explicit MURB (Part 3 apartment scale) --------------------------------
    ("condominium", r"condo"),
    ("apartment", r"apartment|appartement|walk-?up|high[\s-]?rise apartment"),
    ("multi_residential", r"multi[\s-]?(res|fam|unit|dwell)|multiple (dwelling|residential)"),
    # --- Part 9 low-rise multi (NOT MURB per owner decision) -------------------
    (
        "low_rise_residential",
        r"duplex|triplex|four[\s-]?plex|multiplex|\bplex\b|semi[\s-]?det|town\s?house|"
        r"town\s?home|\brow\b|row[\s-]?hous|two[\s-]?unit|2[\s-]?unit|three[\s-]?unit|"
        r"3[\s-]?unit|jumel",
    ),
    # --- Single-family / detached (NOT MURB) -----------------------------------
    (
        "residential_single",
        r"single[\s-]?fam|single[\s-]?unit|single[\s-]?dwell|single-?family|"
        r"detached (house|home|dwelling)|^detached( \+ su)?$|\bhouse\b|\bmaison\b",
    ),
    # --- Mixed use (context; needs other evidence) -----------------------------
    ("mixed_use", r"mixed[\s-]?use|résidentiel et commercial|resid.* et commerc|res.*/.*comm"),
    # --- Non-residential --------------------------------------------------------
    (
        "institutional",
        r"school|école|ecole|church|worship|église|eglise|hospital|hôpital|univers|college|collège|"
        r"government|municipal|fire station|police|arena|recreation|library|ambulance|"
        r"institution|\bpublic\b|séparée|separate (elementary|high)",
    ),
    ("industrial", r"industrial|industriel|factory|manufactur|extraction|silo|grain elevator"),
    (
        "commercial",
        r"commercial|retail|\boffice\b|\bstore\b|\bshop\b|restaurant|\bbar\b|warehouse|"
        r"hotel|motel|magasin|bureau|service",
    ),
    (
        "other",
        r"garage|shed|remise|annexe|barn|grange|outbuilding|accessory|accessoire|ancillary|"
        r"\bkiln\b|greenhouse|serre|pool|piscine|washroom|seasonal|park\b|cabin|camp\b|"
        r"utility|\bfarm\b|agricultur|storage|gazebo|deck|carport",
    ),
    # --- Generic residential (context only; NOT MURB on type alone) ------------
    ("residential", r"residential|résiden|residen|residence|logement|habitation|dwelling"),
]

# Values that are genuinely ambiguous and must stay UNMAPPED (insufficient information).
AMBIGUOUS = {"general", "unknown", "unclassified", "other", "divers", "autre", "n/a", "na", "tbd"}


def propose_category(value: str) -> str | None:
    """Return a proposed normalized category, or None if unmapped/ambiguous."""
    v = value.strip().lower()
    if v in AMBIGUOUS:
        return None
    for category, pattern in RULES:
        if re.search(pattern, v):
            return category
    return None


def main() -> None:
    if not WORKSHEET.exists():
        raise SystemExit(
            f"Missing {WORKSHEET}. Run scripts/build_type_mapping_worksheet.py first."
        )

    df = pd.read_csv(WORKSHEET, dtype={"type_value": str})
    df["proposed_category"] = df["type_value"].apply(propose_category)
    df["proposed_murb_positive"] = df["proposed_category"].isin(MURB_POSITIVE)

    # Full review CSV (every observed value).
    review_cols = [
        "type_value",
        "total_count",
        "pct_of_typed",
        "cumulative_pct",
        "provinces",
        "currently_mapped_to",
        "proposed_category",
        "proposed_murb_positive",
    ]
    df[review_cols].to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    # Build grouped mapping for ALL confidently categorized observed values.
    mapped = df[df["proposed_category"].notna()]
    grouped: dict[str, list[str]] = {}
    for _, r in mapped.sort_values("total_count", ascending=False).iterrows():
        grouped.setdefault(str(r["proposed_category"]), []).append(str(r["type_value"]))

    reviewed_vals = (
        mapped[mapped["total_count"] >= REVIEWED_MIN_COUNT]
        .sort_values("total_count", ascending=False)["type_value"]
        .astype(str)
        .tolist()
    )

    ambiguous_vals = (
        df[df["proposed_category"].isna() & (df["total_count"] >= REVIEWED_MIN_COUNT)]
        .sort_values("total_count", ascending=False)["type_value"]
        .astype(str)
        .tolist()
    )

    doc = {
        "version": "1.0.0",
        "status": "active",
        "provenance": (
            "Generated by scripts/propose_type_normalization.py from the full-population "
            "schema audit (outputs/reports/schema_audit_frequencies.csv). Owner decision "
            "2026-07-30."
        ),
        "murb_definition": (
            "NBC Part 3 multi-unit residential (4+ storeys or > 600 m2 building area). "
            "Part 9 low-rise (duplex, semi, townhouse, row, two-unit, single-family) is NOT a MURB."
        ),
        "murb_positive_categories": list(MURB_POSITIVE),
        "non_murb_categories": list(NON_MURB_CATEGORIES),
        "context_categories": list(CONTEXT_CATEGORIES),
        "note": (
            "Only apartment/multi_residential/condominium are positive MURB evidence from type "
            "alone, and they still require a storey/unit check to be confirmed. 'residential' "
            "and 'mixed_use' are context and require storey/height/unit evidence to qualify."
        ),
        "reviewed_high_frequency": reviewed_vals,
        "mapping": {k: grouped[k] for k in sorted(grouped)},
        "unmapped_ambiguous": ambiguous_vals,
    }

    OUT_YAML.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_YAML, "w", encoding="utf-8") as f:
        f.write("# Active type normalization — loaded by murb_geometry.classification.classifier.\n")
        f.write("# Generated by scripts/propose_type_normalization.py from observed ODB values.\n")
        f.write("# Regenerate after re-running `murb-geometry audit-schema`.\n\n")
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False, width=100)

    # ---- Console summary -----------------------------------------------------
    total_typed = int(df["total_count"].sum())
    mapped_records = int(df.loc[df["proposed_category"].notna(), "total_count"].sum())
    positive_records = int(df.loc[df["proposed_murb_positive"], "total_count"].sum())
    print("=" * 78)
    print("  DRAFT TYPE NORMALIZATION — proposed (Part 3 MURB definition)")
    print("=" * 78)
    print(f"  Typed records                    : {total_typed:,}")
    print(
        f"  Proposed mapped (any category)   : {mapped_records:,} "
        f"({100.0 * mapped_records / max(total_typed, 1):.1f}%)  "
        f"[was {100.0 * int(df.loc[df['currently_mapped_to'] != 'UNMAPPED -> dropped', 'total_count'].sum()) / max(total_typed, 1):.1f}%]"
    )
    print(
        f"  Proposed POSITIVE MURB (type)    : {positive_records:,} "
        f"({100.0 * positive_records / max(total_typed, 1):.1f}%)  "
        "= apartment/multi_residential/condominium only"
    )
    print()
    print("  Records by proposed category:")
    by_cat = (
        df.dropna(subset=["proposed_category"])
        .groupby("proposed_category")["total_count"]
        .sum()
        .sort_values(ascending=False)
    )
    for cat, cnt in by_cat.items():
        flag = "  <-- MURB+" if cat in MURB_POSITIVE else ""
        print(f"    {cat:<22} {int(cnt):>10,}{flag}")
    unmapped = int(df.loc[df["proposed_category"].isna(), "total_count"].sum())
    print(f"    {'(unmapped/ambiguous)':<22} {unmapped:>10,}")
    print()
    print(f"  Active mapping : {OUT_YAML}  ({len(mapped)} mapped values)")
    print(f"  Review sheet   : {OUT_CSV}  (all {len(df)} values)")
    print("=" * 78)


if __name__ == "__main__":
    main()
