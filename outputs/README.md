# Outputs Directory

All generated outputs from the analytical workflow are stored here.
These files are regenerable and excluded from version control.

## Structure

```
outputs/
├── README.md         ← This file (tracked)
├── reports/          ← Data-quality reports and run manifests
├── excel/            ← Formatted Excel workbooks
├── figures/          ← Static charts and plots
├── maps/             ← Map outputs (HTML, PNG)
├── archetypes/       ← Representative archetype definitions
└── gbxml/            ← gbXML simulation geometry files
```

## Regeneration

All outputs can be regenerated from source data using:

```bash
murb-geometry run --config config/default.yaml
```

Or individually:

```bash
murb-geometry excel --config config/default.yaml
murb-geometry archetypes --config config/default.yaml
murb-geometry gbxml --config config/default.yaml
```

## Versioning

Outputs are not committed to Git. Each run generates a manifest
documenting inputs, configuration, and software versions used.
