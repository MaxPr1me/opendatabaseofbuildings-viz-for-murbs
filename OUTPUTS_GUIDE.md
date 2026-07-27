# What This Project Produces — A Simple Guide

This document explains every output file in plain language.

---

## Quick Numbers (What We Found)

- **14.4 million** buildings in the database total
- **7,567** confirmed apartment buildings identified across 5 provinces
- **389 m²** is the national median MURB footprint (about 20m × 19m)
- **1.89** is the national median aspect ratio (slightly longer than wide)
- **5 provinces** have enough data to identify apartments: NS, NB, ON, BC, AB
- **25 per-province archetypes** (5 per province)
- **8 national archetypes** represent the full MURB variety
- **32 gbXML files** ready for energy simulation

---

## Summary of All Outputs

| Output | What it is | Where |
|--------|-----------|-------|
| **Complete Analysis** | Full stats + archetypes for each province | `outputs/reports/complete_analysis.json` |
| **Excel Report** | Formatted spreadsheet of all results | `outputs/excel/complete_murb_analysis.xlsx` |
| **Publication Figures** | 8 PNG charts for papers | `outputs/figures/*.png` |
| **Per-Province gbXML** | 3D models per archetype per province | `outputs/gbxml/` (32 files) |
| **National Archetypes** | 8 "typical building" definitions | In `complete_analysis.json` |
| **Streamlit App** | Interactive web dashboard | `streamlit run app/streamlit_app.py` |
| **Methodology Report** | Written explanation | `outputs/reports/methodology_report.txt` |

---

## Detailed Explanations

### Excel Reports (`outputs/excel/`)

**What they are:** Formatted spreadsheets you can open in Microsoft Excel or Google Sheets.

**What's inside:**
- **Data Quality tab** — Shows which provinces have what information (colour-coded: green = lots of data, red = almost none)
- **MURB Summary tab** — Statistics about apartment buildings (how big, what shape)
- **Field Dictionary tab** — Explains what every column means

**Who uses these:** Anyone who wants to look at the data without writing code.

---

### Publication Figures (`outputs/figures/`)

**What they are:** PNG images of charts, ready to paste into a report or presentation.

| Figure | What it shows |
|--------|--------------|
| `fig1_completeness_heatmap.png` | Which provinces have which data fields filled in |
| `fig2_area_by_province.png` | All-building sizes by province (sampled) |
| `fig3_ns_murb_area_distribution.png` | NS MURB size range (percentiles) |
| `fig4_archetype_comparison.png` | NS archetype area + aspect ratio |
| `fig5_classification_pie.png` | National classification breakdown |
| `province_murb_area.png` | **MURB** median footprint by province with IQR |
| `national_archetypes_scatter.png` | 8 national archetypes plotted (area vs AR) |
| `province_archetypes_comparison.png` | All 25 per-province archetypes side-by-side |

---

### Archetype Definitions (`outputs/archetypes/`)

**What they are:** Descriptions of "typical" apartment buildings found by grouping similar ones together.

**How it works:** We measured 7,567 actual apartment buildings across 5 provinces, then used a math technique called "clustering" to group similar buildings. Each group has a "representative" — an actual building that best represents its group.

**Example archetypes from our results:**

| Type | Size | Shape | Count |
|------|------|-------|-------|
| Small compact | 243 m² | Nearly square | 2,580 buildings |
| Medium standard | 369 m² | Slightly elongated | 2,597 buildings |
| Medium elongated | 579 m² | Long and narrow | 1,370 buildings |
| Large complex | 5,105 m² | Wide building | 57 buildings |

**Why this matters:** Energy modellers need to know "what does a typical Canadian apartment look like?" These archetypes answer that question with real data.

---

### gbXML Files (`outputs/gbxml/`)

**What they are:** 3D building geometry files that energy simulation software can read.

**What's inside each file:**
- A simplified 3D box representing a typical apartment building
- Walls, floor, and roof surfaces with proper orientations (north, south, east, west)
- Multiple storeys (4 floors standard)
- Correct dimensions based on real measured buildings

**Files produced (5 archetypes per province = 25 files, plus earlier ones):**

| Province | Archetypes | Largest (most common) |
|----------|-----------|----------------------|
| NS | ns_ns_a01.xml through ns_ns_a05.xml | NS-A02: 231 m², n=908 (45%) |
| NB | nb_nb_a01.xml through nb_nb_a05.xml | NB-A05: 297 m², n=947 (47%) |
| ON | on_on_a01.xml through on_on_a05.xml | ON-A05: 300 m², n=906 (48%) |
| BC | bc_bc_a01.xml through bc_bc_a05.xml | BC-A02: 957 m², n=136 (35%) |
| AB | ab_ab_a01.xml through ab_ab_a05.xml | AB-A01: 332 m², n=431 (34%) |

**Who uses these:** Researchers who run building energy simulations in OpenStudio or EnergyPlus.

**Important limitation:** These are simplified rectangular extrusions. Real buildings have balconies, setbacks, and irregular shapes. The gbXML gives a data-driven starting point.

---

### Streamlit Visualization (`app/streamlit_app.py`)

**What it is:** An interactive web page that runs on your computer.

**What you can do:**
- Filter by province, building size, number of floors
- See a table of all inventoried files
- View data quality information

**How to launch:** `streamlit run app/streamlit_app.py` (opens in your web browser)

---

### Clustering (Archetype Generation)

**What it is:** A mathematical technique to find natural groups in the data.

**How it works (simplified):**
1. We measure every apartment building: how big is the footprint? How long and narrow? How complex is the shape?
2. We plot all buildings in a "feature space" (imagine a 3D scatter plot)
3. A clustering algorithm (K-means) finds groups of buildings that are close together
4. For each group, we pick the one building that's most "in the middle" — the **medoid**
5. That medoid building becomes the **representative archetype** for its group

**Why not just average?** Averaging polygon coordinates from different buildings produces meaningless shapes. Instead, we pick an actual real building that best represents each group.

---

### JSON Reports (`outputs/reports/`)

**What they are:** Machine-readable data files (text format) containing all the numbers.

| File | Contains |
|------|----------|
| `inventory.json` | Every data file: size, record count, completeness percentages |
| `all_provinces_murb_analysis.json` | Per-province apartment statistics and archetypes |
| `classification_summary.json` | How many buildings fall into each confidence category |
| `summary_stats.json` | National geometry numbers (area, shape, compactness) |
| `ns_murb_analysis.json` | Detailed Nova Scotia apartment characterization |
| `national_murb_analysis.json` | Combined multi-province analysis |
| `methodology_report.txt` | Human-readable methodology writeup |

---

## What the Numbers Mean

| Metric | What it measures | Example |
|--------|-----------------|---------|
| **Footprint area (m²)** | How much ground the building covers | 383 m² = about 40m × 10m |
| **Aspect ratio** | How elongated the building is (1 = square, 4 = very long) | 1.87 = slightly longer than wide |
| **Compactness** | How "circle-like" the shape is (1 = circle, 0 = very complex) | 0.6 = moderately compact |
| **Rectangularity** | How well it fills its bounding box (1 = perfect rectangle) | 0.85 = mostly rectangular |
| **Units** | Number of apartments in the building | 12 = typical small MURB |

---

## Quick Numbers (What We Found)

- **14.4 million** buildings in the database total
- **7,567** confirmed apartment buildings identified across 5 merged provinces
- **389 m²** is the national median MURB footprint
- **1.89** is the national median aspect ratio
- **5 provinces** have enough data: NS, NB, ON (merged 3 files), BC, AB
- **25 per-province archetypes** (5 per province via K-means clustering)
- **8 national archetypes** from combined clustering
- **32 gbXML files** for energy simulation

---

## How to Reproduce Everything

```bash
# One command to regenerate all outputs:
python scripts/complete_run.py
```
