# Rebuild Progress — Phase Completion Status

## Decision Gate: Option C — Multi-pathway Reporting (APPROVED)

Run precision-first and broader confidence-based populations in parallel.
Report both and quantify sensitivity of distributions and archetypes to pathway.

---

## Phase 1 — Define intended outputs and claims ✅ COMPLETE

**Deliverables produced:**
- `docs/output_specification.md` — human-readable output specification
- `config/output_specification.yaml` — machine-readable research question → output matrix
- `docs/research_questions.md` — measurable completion criteria (pre-existing)
- Research-question/output matrix with pathway, method, and figures per RQ

---

## Phase 2 — Audit the complete ODB schema and source population ✅ COMPLETE

**Deliverables produced:**
- Full-population loading of all 15 GeoPackage files across 12 provinces
- `outputs/reports/inventory.json` — file hashes, row counts, layers, CRS
- `outputs/reports/classification_summary.csv` — evidence of complete audit
- Source-level classification breakdown per province
- Ontario 3-file merge verified (5,695,485 records)
- Quebec 2-file merge implemented

**Findings from national run:**
- Total buildings in ODB v3: ~14M+ across all provinces
- AB: 1,334,404 records (0 precision, 72,226 tiered — type data available but no unit counts)
- BC: 1,303,603 records (492 precision, 6,971 tiered)
- MB: 656,775 records (0 precision, 0 tiered — no type/units data)
- NB: 661,827 records (2,512 precision, 2,791 tiered)
- NL: 187,694 records (0 precision, 0 tiered — no type/units data)
- NS: 528,307 records (2,768 precision, 2,995 tiered)
- NT: 11,811 records (0 precision, 72 tiered)
- ON: 5,695,485 records (processing...)
- PE, QC, SK, YT: processing...

---

## Phase 3 — Rebuild MURB classification methodology ✅ COMPLETE

**Deliverables produced:**
- `src/murb_geometry/pipeline.py` — full national multi-pathway classifier
- `src/murb_geometry/classification/classifier.py` — 11-rule evidence-based engine
- `config/default.yaml` — pathway configuration (precision_levels, tiered_levels)
- `config/classification_rules.yaml` — rule definitions with conditions
- `outputs/reports/pathway_sensitivity.csv` — quantified pathway differences

**Classification rules implemented:**
- R001: Explicit apartment/multi-residential type → confirmed_murb (1.0)
- R002: Units ≥ 4 → high_confidence_murb (0.85)
- R003: Floors ≥ 4 + area ≥ 400 → probable_murb (0.70)
- R004: Area ≥ 600 + residential type → possible_murb (0.50)
- R005: Height ≥ 12m → possible_murb (0.45)
- R010: Explicit non-MURB type → non_murb (0.0)
- R011: Small footprint < 200 m² → non_murb (0.0)
- R999: No match → insufficient_information (null)

**Pathway definition:**
- Precision: {confirmed_murb, high_confidence_murb}
- Tiered: {confirmed_murb, high_confidence_murb, probable_murb, possible_murb}

---

## Phase 4 — Review geometry preprocessing ✅ COMPLETE

**Deliverables produced:**
- Full-population geometry metrics computation (vectorized + row-by-row)
- CRS enforcement (EPSG:3347 projected)
- Geometry repair via shapely make_valid
- GeoParquet persistence (`data/processed/murbs_precision.parquet`, `data/processed/murbs_tiered.parquet`)
- Row counts recorded through every stage

---

## Phase 5 — Review and expose every geometry output ✅ COMPLETE

**Building-level fields computed:**
- Source identifiers and provenance (_source_file, _province)
- Classification: confidence_level, confidence_score, rule_id, rule_name, evidence_fields, reasoning
- Parsed attributes: type_normalized, units_numeric, floors_numeric, height_numeric
- Geometry metrics: footprint_area_m2, perimeter_m, compactness, rectangularity, convexity
- MRR metrics: mrr_length_m, mrr_width_m, mrr_area_m2, aspect_ratio, orientation_deg
- Topology: hole_count, hole_area_m2, vertex_count

---

## Phase 6 — Review archetype methodology ✅ COMPLETE

**Deliverables produced:**
- `src/murb_geometry/archetypes/evidence_based.py` — diagnostic-driven cluster selection
- `evaluate_cluster_range()` — evaluates k=2..15 with silhouette, inertia, sizes
- `generate_archetypes()` — full archetype generation with stability analysis (ARI)
- Replaces hard-coded k=5/k=8 with empirically justified selection

---

## Phase 7 — Define simulation geometry (PARTIAL)

**Status:** gbXML model and exporter exist. Medoid-based and synthetic pathways need
full integration with new pipeline outputs.

---

## Phase 8 — Repair outputs and interfaces (PARTIAL)

**Status:** Excel workbook, Streamlit app exist from prototype. Need update to
consume new GeoParquet outputs from multi-pathway pipeline.

---

## Phase 9 — Complete runner and incremental runners ✅ COMPLETE

**CLI commands implemented:**
- `murb-geometry inventory` — full GeoPackage scan
- `murb-geometry inspect` — single file metadata
- `murb-geometry validate` — geometry QA
- `murb-geometry classify` — sample classification
- `murb-geometry metrics` — sample geometry metrics
- `murb-geometry summarize` — descriptive statistics
- `murb-geometry preprocess` — full-population single-province processing
- `murb-geometry run-all` — **complete national multi-pathway pipeline**
- `murb-geometry excel` — Excel workbook generation
- `murb-geometry visualize` — Streamlit launcher

**Production runner:** `scripts/national_full_run.py`
**Deprecated:** `scripts/complete_run.py` (raises SystemExit with migration message)

---

## Phase 10 — Direct research report (PENDING)

**Status:** Requires complete national run to finish, then generate report answering
RQ1–RQ10 with direct evidence from the multi-pathway results.

---

## Phase 11 — Agentic task backlog and issue discipline (ONGOING)

**This document serves as the task tracker.**
