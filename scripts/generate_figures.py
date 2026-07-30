"""Generate publication figures from persisted national-run outputs.

Thin wrapper around ``murb_geometry.visualization.charts.build_all_figures`` so the
figures always reflect the current pipeline outputs (run manifest + MURB subsets).
Run ``murb-geometry run-all`` first.
"""

import logging

from murb_geometry.visualization.charts import build_all_figures

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

if __name__ == "__main__":
    paths = build_all_figures()
    print(f"Wrote {len(paths)} figures to outputs/figures/")
    for p in paths:
        print(f"  {p}")
