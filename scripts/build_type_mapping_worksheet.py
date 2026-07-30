"""Build a `type`-value mapping decision worksheet from the schema audit.

Consumes the persisted schema-audit frequency table (produced by
`murb-geometry audit-schema`) and produces a reviewer-facing worksheet that
lists every distinct source `type` value, its record coverage, the provinces
it appears in, and what the CURRENT hard-coded normalization map does with it
(matched category vs. silently dropped).

This script INVENTS NOTHING. It only reports observed values and the behaviour
of the existing code, so the mapping decisions can be made from evidence.

Outputs:
    outputs/reports/type_mapping_worksheet.csv  — one row per distinct type value
    outputs/reports/type_coverage_by_province.csv — typed vs mapped coverage per province

Usage:
    python scripts/build_type_mapping_worksheet.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from murb_geometry.classification.classifier import normalize_type_value

FREQ_CSV = Path("outputs/reports/schema_audit_frequencies.csv")
OUT_WORKSHEET = Path("outputs/reports/type_mapping_worksheet.csv")
OUT_COVERAGE = Path("outputs/reports/type_coverage_by_province.csv")

# Values that are missing, not real categories.
MISSING_VALUES = {"..", "", "<NULL>", "NA", "N/A", "nan", "None"}

# Normalized categories that currently reach a POSITIVE MURB rule
# (R001 confirmed; R004 possible via residential/mixed_use). This mirrors
# classifier.classify_building so we can show which mapped values actually
# contribute MURB evidence today.
POSITIVE_TYPE_CATEGORIES = {
    "apartment",
    "multi_residential",
    "condominium",  # R001 -> confirmed_murb
    "residential",
    "mixed_use",  # R004 -> possible_murb (only with area >= 600)
}


def main() -> None:
    if not FREQ_CSV.exists():
        raise SystemExit(
            f"Missing {FREQ_CSV}. Run `murb-geometry audit-schema` first to generate it."
        )

    df = pd.read_csv(FREQ_CSV, dtype={"value": str})
    types = df[df["field"] == "type"].copy()
    if types.empty:
        raise SystemExit("No `type` rows found in the frequency table.")

    types["value"] = types["value"].fillna("<NULL>")
    types["is_missing"] = types["value"].str.strip().isin(MISSING_VALUES)

    # ---- Per-province coverage (typed vs. currently mapped) -------------------
    coverage_rows: list[dict[str, object]] = []
    for prov, grp in types.groupby("province"):
        typed = int(grp.loc[~grp["is_missing"], "count"].sum())
        missing = int(grp.loc[grp["is_missing"], "count"].sum())
        real = grp[~grp["is_missing"]].copy()
        real["mapped"] = real["value"].apply(normalize_type_value)
        mapped_records = int(real.loc[real["mapped"].notna(), "count"].sum())
        positive_records = int(
            real.loc[real["mapped"].isin(POSITIVE_TYPE_CATEGORIES), "count"].sum()
        )
        coverage_rows.append(
            {
                "province": prov,
                "records_with_type": typed,
                "records_missing_type": missing,
                "records_type_mapped": mapped_records,
                "records_type_unmapped": typed - mapped_records,
                "pct_type_mapped": round(100.0 * mapped_records / max(typed, 1), 2),
                "records_positive_murb_type": positive_records,
                "distinct_type_values": int((~grp["is_missing"]).sum()),
            }
        )
    coverage = pd.DataFrame(coverage_rows).sort_values("records_with_type", ascending=False)

    # ---- Aggregate distinct values across provinces --------------------------
    real = types[~types["is_missing"]].copy()
    agg = (
        real.groupby("value")
        .agg(
            total_count=("count", "sum"),
            n_provinces=("province", "nunique"),
            provinces=("province", lambda s: ";".join(sorted(set(s)))),
        )
        .reset_index()
        .rename(columns={"value": "type_value"})
        .sort_values("total_count", ascending=False)
        .reset_index(drop=True)
    )

    total_typed = int(agg["total_count"].sum())
    agg["pct_of_typed"] = (100.0 * agg["total_count"] / max(total_typed, 1)).round(4)
    agg["cumulative_pct"] = agg["pct_of_typed"].cumsum().round(4)

    # Province with the most records for each value.
    top_prov = (
        real.sort_values("count", ascending=False)
        .drop_duplicates("value")
        .set_index("value")["province"]
    )
    agg["top_province"] = agg["type_value"].map(top_prov)

    # What the CURRENT code does with each value.
    agg["currently_mapped_to"] = agg["type_value"].apply(
        lambda v: normalize_type_value(v) or "UNMAPPED -> dropped"
    )
    agg["currently_murb_evidence"] = agg["type_value"].apply(
        lambda v: "yes" if normalize_type_value(v) in POSITIVE_TYPE_CATEGORIES else "no"
    )

    # Blank decision columns for the reviewer to fill in.
    agg["decision_category"] = ""
    agg["decision_is_murb_evidence"] = ""
    agg["reviewer_notes"] = ""

    OUT_WORKSHEET.parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(OUT_WORKSHEET, index=False, encoding="utf-8-sig")
    coverage.to_csv(OUT_COVERAGE, index=False, encoding="utf-8-sig")

    # ---- Console summary -----------------------------------------------------
    unmapped = agg[agg["currently_mapped_to"] == "UNMAPPED -> dropped"]
    unmapped_records = int(unmapped["total_count"].sum())
    print("=" * 78)
    print("  TYPE-VALUE MAPPING WORKSHEET — grounded in schema_audit_frequencies.csv")
    print("=" * 78)
    print(f"  Distinct non-missing type values : {len(agg):,}")
    print(f"  Records with a type value        : {total_typed:,}")
    print(
        f"  Currently UNMAPPED (dropped)     : {unmapped_records:,} records "
        f"({100.0 * unmapped_records / max(total_typed, 1):.1f}%) "
        f"across {len(unmapped):,} distinct values"
    )
    print()
    print("  Top 20 CURRENTLY-UNMAPPED type values by record count:")
    for _, r in unmapped.head(20).iterrows():
        print(
            f"    {r['total_count']:>10,}  {r['pct_of_typed']:>5.2f}%  "
            f"[{r['provinces']}]  {r['type_value']!r}"
        )
    print()
    print("  Per-province type coverage (records_type_mapped / records_with_type):")
    for _, r in coverage.iterrows():
        print(
            f"    {r['province']:>2}: typed={r['records_with_type']:>9,}  "
            f"mapped={r['pct_type_mapped']:>5.1f}%  "
            f"positive_murb_type={r['records_positive_murb_type']:>7,}"
        )
    print()
    print(f"  Worksheet : {OUT_WORKSHEET}")
    print(f"  Coverage  : {OUT_COVERAGE}")
    print("=" * 78)


if __name__ == "__main__":
    main()
