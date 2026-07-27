# Architecture Decision Records

## ADR-001: Use GeoParquet for Intermediate Storage

**Status:** Accepted

**Context:** The national dataset has ~14.4M records across 15 GeoPackage files (~6.3 GB). Processing requires efficient columnar reads, spatial filtering, and partitioning.

**Decision:** Use GeoParquet as the intermediate analytical format, partitioned by province and source organization.

**Rationale:**
- Columnar format enables predicate pushdown and column projection
- Partitioning by province allows incremental processing
- Compatible with DuckDB spatial extension for analytical queries
- Widely supported in the Python geospatial ecosystem
- Faster read times than GeoPackage for analytical workloads

**Consequences:**
- Requires conversion step from source GeoPackage
- Additional disk space for intermediate files
- Raw GeoPackage files preserved unchanged

---

## ADR-002: Province-Level Processing

**Status:** Accepted

**Context:** Loading all 14.4M records simultaneously exceeds practical memory limits for many workstations.

**Decision:** Process data province-by-province, storing intermediate results in partitioned GeoParquet.

**Rationale:**
- Largest single province file (ON combined) is ~5.7M records
- Province is a natural analytical partition
- Enables incremental processing and resumable runs
- National aggregation performed on summaries, not raw records

**Consequences:**
- Cross-province spatial operations (e.g., boundary buildings) need special handling
- National statistics computed from provincial summaries

---

## ADR-003: Typed Configuration with Pydantic

**Status:** Accepted

**Context:** Research decisions (thresholds, boundaries, methods) must be configurable, validated, and documented.

**Decision:** Use Pydantic models for configuration with YAML serialization and local override support.

**Rationale:**
- Type validation catches configuration errors early
- Self-documenting through type annotations
- YAML is human-readable and diff-friendly
- Local override pattern (local.yaml) avoids editing shared config

**Consequences:**
- Configuration changes require model updates
- Slightly more complex than plain dictionaries
