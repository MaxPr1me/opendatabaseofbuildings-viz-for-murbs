# What This Project Produces — A Simple Guide

This document explains every output file in plain language.

---

## Summary of All Outputs

| Output | What it is | Where to find it |
|--------|-----------|-----------------|
| **Inventory Report** | List of every data file with completeness stats | `outputs/reports/inventory.json` |
| **Province MURB Analysis** | Size/shape stats for apartments in each province | `outputs/reports/all_provinces_murb_analysis.json` |
| **Classification Results** | How many buildings we think are apartments | `outputs/reports/classification_summary.json` |
| **National Summary Stats** | Median size, shape numbers for all buildings | `outputs/reports/summary_stats.json` |
| **Methodology Report** | Written explanation of what was done and found | `outputs/reports/methodology_report.txt` |
| **Excel Reports** | Spreadsheets you can open without coding | `outputs/excel/` |
| **Publication Figures** | Charts ready for papers/presentations | `outputs/figures/` |
| **Archetype Definitions** | "Typical" apartment building descriptions | `outputs/archetypes/` |
| **gbXML Files** | 3D building models for energy simulation | `outputs/gbxml/` |
| **Streamlit App** | Interactive web dashboard (run locally) | `app/streamlit_app.py` |

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
| `fig2_area_by_province.png` | Building sizes in each province (bar chart with error bars) |
| `fig3_ns_murb_area_distribution.png` | How big Nova Scotia apartments are (from tiny to huge) |
| `fig4_archetype_comparison.png` | The 6 "typical" building types we found |
| `fig5_classification_pie.png` | What fraction of buildings are apartments vs. houses vs. unknown |

---

### Archetype Definitions (`outputs/archetypes/`)

**What they are:** Descriptions of "typical" apartment buildings found by grouping similar ones together.

**How it works:** We measured 8,788 actual apartment buildings, then used a math technique called "clustering" to group similar buildings. Each group has a "representative" — an actual building that best represents its group.

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
- Multiple storeys (usually 4 floors)
- Correct dimensions based on real measured buildings

**Files produced (one per province):**
- `ns_archetype.xml` — Nova Scotia representative (most data)
- `nb_archetype.xml` — New Brunswick representative
- `on_2_archetype.xml` — Ontario representative (region 2)
- `on_3_archetype.xml` — Ontario representative (region 3)
- `bc_archetype.xml` — British Columbia representative
- `ab_archetype.xml` — Alberta representative

**Who uses these:** Researchers who run building energy simulations in OpenStudio or EnergyPlus. They import these files to simulate heating/cooling energy use for typical apartments.

**Important limitation:** These are simplified boxes. Real buildings have balconies, setbacks, and irregular shapes. The gbXML gives a starting point for simulation, not a perfect model.

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
- **8,788** confirmed apartment buildings identified across 6 provinces
- **383 m²** is the national median MURB footprint
- **1.87** is the national median aspect ratio (slightly elongated)
- **12 units** is the median apartment count (Nova Scotia data)
- **6 provinces** have enough data to identify apartments
- **8 archetypes** represent the national MURB variety
