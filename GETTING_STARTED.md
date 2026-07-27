# Getting Started — Step by Step

A plain-language guide to running this project and getting outputs.

---

## What Does This Project Do?

This project looks at **building footprints** (the shape of buildings as seen from above) across Canada and figures out which ones are **apartment buildings** (MURBs — Multi-Unit Residential Buildings). It measures them, groups similar ones together, and produces reports you can open in Excel or view in a web browser.

---

## Prerequisites

You need:
- **Windows, Mac, or Linux** computer
- **Python 3.12** or newer installed
- **uv** (a fast Python package manager) — [install it here](https://docs.astral.sh/uv/getting-started/installation/)
- The **data files** already placed in the `data/` folder (GeoPackage files from Statistics Canada)

---

## Step 1: Open a Terminal

- **Windows:** Open PowerShell or Command Prompt
- **Mac/Linux:** Open Terminal

Navigate to the project folder:
```bash
cd path/to/opendatabaseofbuildings-viz-for-murbs
```

---

## Step 2: Create the Environment and Install

```bash
uv venv --python 3.12 .venv
```
This creates a virtual environment (a sandbox for the project's tools).

Then install everything:
```bash
uv pip install -e ".[dev]"
```
Wait for it to finish downloading packages.

---

## Step 3: Activate the Environment

**Windows PowerShell:**
```powershell
.venv\Scripts\activate
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

Your prompt should now show `(.venv)` at the start.

---

## Step 4: Inspect a Data File

Pick any province file and look at what's inside:

```bash
murb-geometry inspect data/ODB_v3_NS/ODB_v3_NS.gpkg
```

This prints a table showing:
- How many buildings are in the file
- What information is available (type, floors, units, height)
- What percentage of records have each field filled in
- Which organizations provided the data

---

## Step 5: Run the Full Inventory

This scans ALL data files and creates a JSON report:

```bash
murb-geometry inventory --no-hash
```

The `--no-hash` flag skips computing file checksums (saves ~30 min on 6 GB of data).

Output goes to: `outputs/reports/inventory.json`

> **Note:** This takes a while on the full national dataset (14.4 million buildings across 6.3 GB). Be patient — you'll see a summary table when it finishes.

---

## Step 6: Generate an Excel Report

```bash
python -c "
from pathlib import Path
import json
from murb_geometry.excel.workbook import create_summary_workbook

inv = json.loads(Path('outputs/reports/inventory.json').read_text())
completeness = []
for f in inv['files']:
    row = {'province': f['province_territory'], 'records': f['total_records']}
    for fc in f['field_completeness']:
        row[fc['field_name'] + '_pct'] = fc['completeness_pct']
    completeness.append(row)

create_summary_workbook(
    Path('outputs/excel/murb_inventory_report.xlsx'),
    completeness_data=completeness,
    metadata={'Source': 'ODB v3', 'Scope': 'National inventory'},
)
print('Done! Open: outputs/excel/murb_inventory_report.xlsx')
"
```

Open the `.xlsx` file in Excel to see:
- **Read Me** tab — what the report contains
- **Data Quality** tab — which provinces have what data (colour-coded)
- **Field Dictionary** tab — what each column means

---

## Step 7: Launch the Visualization App

```bash
streamlit run app/streamlit_app.py
```

A web browser tab opens automatically. You'll see:
- Province filter checkboxes
- A summary of all data files
- Tabs for maps, charts, and quality data

Press `Ctrl+C` in the terminal to stop it.

---

## Step 8: Run the Tests (Optional)

To verify everything is working:
```bash
pytest tests/
```

You should see: `83 passed`

---

## Where Are My Outputs?

| What | Where |
|------|-------|
| Inventory report (JSON) | `outputs/reports/inventory.json` |
| Excel workbook | `outputs/excel/murb_inventory_report.xlsx` |
| Streamlit app | Opens in your browser (not saved as a file) |
| Figures (when generated) | `outputs/figures/` |
| Maps (when generated) | `outputs/maps/` |

---

## Example Questions and Answers

### Q: How many buildings are in the database?
**A:** About 14.4 million across all provinces and territories. Run `murb-geometry inventory --no-hash` to get the exact count.

### Q: Which province has the best data for identifying apartments?
**A:** Nova Scotia — it has 23% of buildings with unit counts filled in (121,592 buildings). Ontario and BC have the most height data. Run `murb-geometry inspect data/ODB_v3_NS/ODB_v3_NS.gpkg` to see the details.

### Q: Can I just look at one province?
**A:** Yes. Every command works on individual files:
```bash
murb-geometry inspect data/ODB_v3_BC/ODB_v3_BC.gpkg
```

### Q: What's a "completeness percentage"?
**A:** It tells you what fraction of buildings have a particular piece of information. For example, if "floors" completeness is 3%, only 3 out of every 100 buildings have the number of storeys recorded. The rest are unknown.

### Q: Why are so many fields empty?
**A:** The database combines data from many different cities and agencies. Some only shared building shapes (from satellite images), while others included detailed property records. Satellite-extracted buildings have geometry but nothing else.

### Q: What does MURB mean?
**A:** Multi-Unit Residential Building — basically an apartment building, condo, or any building with 4+ dwelling units.

### Q: Can this tell me window sizes?
**A:** No. Building footprints are just the roof outline seen from above. You can't determine windows from that. The project supports adding window assumptions for simulation, but they come from other sources or standards — not from this data.

### Q: What's the coordinate system?
**A:** EPSG:3347 (NAD83 / Statistics Canada Lambert). It's a projected system in metres, covering all of Canada, so area and distance calculations work correctly.

### Q: I only want to process the small files for testing. Which ones?
**A:** The three smallest are:
- `ODB_v3_NT.gpkg` — Northwest Territories (12K records, 5 MB)
- `ODB_v3_YT.gpkg` — Yukon (12K records, 5 MB)
- `ODB_v3_PE.gpkg` — Prince Edward Island (86K records, 35 MB)

### Q: What's next after this?
**A:** The roadmap in `docs/roadmap.md` has 8 phases. The code currently handles inventory, geometry measurement, classification, and reporting. Future phases add data enrichment, archetype selection, and simulation file export (gbXML for EnergyPlus/OpenStudio).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `murb-geometry` not found | Make sure the venv is activated (Step 3) |
| `ModuleNotFoundError` | Run `uv pip install -e ".[dev]"` again |
| Inventory takes too long | Use `--no-hash` flag, or inspect files one at a time |
| Excel file won't open | Make sure `outputs/reports/inventory.json` exists first (Step 5) |
| Streamlit shows "no data" | Run the inventory command first (Step 5) |
